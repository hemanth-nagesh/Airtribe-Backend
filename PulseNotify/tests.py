from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from pulsenotify.task import check_prices, send_notification
from user.models import notification, priceAlert


class _DummyPriceResponse:
    def __init__(self, price, status_code=200):
        self._price = price
        self.status_code = status_code

    def json(self):
        return {"price": self._price}


class PriceThresholdTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="threshold_user", password="pass")

    def _create_alert(self, threshold_price):
        return priceAlert.objects.create(
            user=self.user,
            orign="DEL",
            destination="BOM",
            treshold_price=threshold_price,
            status=priceAlert.Status.ACTIVE,
        )

    def test_price_below_threshold_triggers_alert(self):
        from unittest.mock import patch

        alert = self._create_alert(threshold_price=4500)

        with patch("pulsenotify.task.requests.get") as get_mock, patch(
            "pulsenotify.task.send_notification.delay"
        ) as delay_mock:
            get_mock.return_value = _DummyPriceResponse(price=4200)

            check_prices()

            delay_mock.assert_called_once()
            called_alert_id, called_price = delay_mock.call_args.args
            self.assertEqual(called_alert_id, alert.id)
            self.assertEqual(float(called_price), 4200.0)

    def test_price_above_threshold_does_not_trigger(self):
        from unittest.mock import patch

        self._create_alert(threshold_price=4500)

        with patch("pulsenotify.task.requests.get") as get_mock, patch(
            "pulsenotify.task.send_notification.delay"
        ) as delay_mock:
            get_mock.return_value = _DummyPriceResponse(price=5000)

            check_prices()

            delay_mock.assert_not_called()

    def test_price_equal_to_threshold_triggers_alert(self):
        from unittest.mock import patch

        alert = self._create_alert(threshold_price=4500)

        with patch("pulsenotify.task.requests.get") as get_mock, patch(
            "pulsenotify.task.send_notification.delay"
        ) as delay_mock:
            get_mock.return_value = _DummyPriceResponse(price=4500)

            check_prices()

            delay_mock.assert_called_once()
            called_alert_id, called_price = delay_mock.call_args.args
            self.assertEqual(called_alert_id, alert.id)
            self.assertEqual(float(called_price), 4500.0)


class NotificationLogTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="log_user", password="pass")
        self.alert = priceAlert.objects.create(
            user=self.user,
            orign="DEL",
            destination="BOM",
            treshold_price=4500,
            status=priceAlert.Status.ACTIVE,
        )

    def test_notification_log_created_with_correct_message(self):
        send_notification(self.alert.id, 4200)

        log = notification.objects.get(trigered_price_alert=self.alert)
        self.assertEqual(log.user, self.user)
        self.assertIn("DEL-BOM", log.message)
        self.assertIn("4200", log.message)
        self.assertIn("4500", log.message)

        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, priceAlert.Status.TRIGGERED)


class AlertScopingTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username="user1", password="pass")
        self.user2 = User.objects.create_user(username="user2", password="pass")

        priceAlert.objects.create(
            user=self.user1,
            orign="DEL",
            destination="BOM",
            treshold_price=4500,
            status=priceAlert.Status.ACTIVE,
        )
        priceAlert.objects.create(
            user=self.user2,
            orign="BLR",
            destination="HYD",
            treshold_price=2000,
            status=priceAlert.Status.ACTIVE,
        )

    def test_user_only_sees_own_alerts(self):
        self.client.force_authenticate(user=self.user1)
        resp = self.client.get("/api/alerts/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["orign"], "DEL")

    def test_user_cannot_see_other_users_alerts(self):
        self.client.force_authenticate(user=self.user1)
        resp = self.client.get("/api/alerts/")
        self.assertEqual(resp.status_code, 200)
        origins = [item["orign"] for item in resp.json()]
        self.assertNotIn("BLR", origins)
