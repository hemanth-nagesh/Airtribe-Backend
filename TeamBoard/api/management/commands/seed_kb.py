from django.core.management.base import BaseCommand

from api.models import KBEntry


class Command(BaseCommand):
    help = 'Seed the knowledge base with sample entries.'

    def handle(self, *args, **options):
        entries = [
            {
                'question': 'What is select_related?',
                'answer': 'select_related() does a SQL join to reduce queries when accessing foreign keys in Django.',
                'category': KBEntry.Category.DATABASE,
            },
            {
                'question': 'When should I use prefetch_related?',
                'answer': 'Use prefetch_related() for many-to-many and reverse foreign keys to avoid N+1 queries.',
                'category': KBEntry.Category.DATABASE,
            },
            {
                'question': 'How does transaction.atomic() work?',
                'answer': 'transaction.atomic() wraps a block in a database transaction and rolls back on exceptions.',
                'category': KBEntry.Category.DATABASE,
            },
            {
                'question': 'What is a JWT token?',
                'answer': 'A JWT is a compact, signed token used for stateless authentication between clients and APIs.',
                'category': KBEntry.Category.API,
            },
            {
                'question': 'How do I refresh a JWT token?',
                'answer': 'Use the refresh token to obtain a new access token before the access token expires.',
                'category': KBEntry.Category.API,
            },
            {
                'question': 'When should I use Q objects?',
                'answer': 'Use Q objects to build complex OR/AND queries, especially when combining conditions.',
                'category': KBEntry.Category.DATABASE,
            },
            {
                'question': 'What is a Django model manager?',
                'answer': 'A model manager is the interface for database queries, like objects or custom managers.',
                'category': KBEntry.Category.FRAMEWORKS,
            },
            {
                'question': 'How do I paginate API results?',
                'answer': 'Use DRF pagination classes to return paged results with count and next/previous links.',
                'category': KBEntry.Category.API,
            },
            {
                'question': 'What is the difference between PUT and PATCH?',
                'answer': 'PUT replaces the full resource, while PATCH updates only provided fields.',
                'category': KBEntry.Category.API,
            },
            {
                'question': 'How does caching help database queries?',
                'answer': 'Caching reduces repeated database hits for common queries and speeds up responses.',
                'category': KBEntry.Category.GENERAL,
            },
        ]

        created = 0
        for entry in entries:
            _, was_created = KBEntry.objects.get_or_create(
                question=entry['question'],
                defaults=entry,
            )
            if was_created:
                created += 1

        self.stdout.write(self.style.SUCCESS(f'Seeded KB entries. Created: {created}'))
