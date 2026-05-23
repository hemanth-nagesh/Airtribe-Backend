from celery import shared_task
import requests
from user.models import priceAlert, notification
 
@shared_task
def check_prices():
    # Get all distinct routes with active alerts
    active_alerts = priceAlert.objects.filter(status=priceAlert.Status.ACTIVE)
    routes = active_alerts.values_list('orign', 'destination').distinct()
 
    for origin, destination in routes:
        route = f'{origin}-{destination}'
 
        # Call your own mock price endpoint
        response = requests.get(
            'http://localhost:8000/api/flights/price/',
            params={'route': route}
 )
        if response.status_code != 200:
            continue
        current_price = response.json().get('price')
 
        # Check each active alert for this route
        route_alerts = active_alerts.filter(orign=origin, destination=destination)
        for alert in route_alerts:
            if current_price is None:
                continue

            if float(current_price) <= float(alert.treshold_price):
                send_notification.delay(alert.id, current_price)
 
@shared_task
def send_notification(alert_id, triggered_price):
    alert = priceAlert.objects.get(id=alert_id)
    message = (f'Price alert triggered! {alert.orign}-{alert.destination} '
               f'is now ₹{triggered_price}  -  below your threshold of '
               f'₹{alert.treshold_price}')
    notification.objects.create(
        user=alert.user,
        trigered_price_alert=alert,
        message=message,
    )
    # Mark alert as triggered so it doesn't fire again
    alert.status = priceAlert.Status.TRIGGERED
    alert.save(update_fields=['status'])