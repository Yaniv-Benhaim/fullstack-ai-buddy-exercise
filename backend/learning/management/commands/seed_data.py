from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from learning.models import UserProfile, Module, UserProgress


class Command(BaseCommand):
    help = "Seed the database with test data for the exercise"

    def handle(self, *args, **options):
        # Create test user (skip if already exists)
        user, created = User.objects.get_or_create(
            username="testuser",
            defaults={
                "email": "test@flyingcargo.com",
            },
        )
        if created:
            user.set_password("testpass123")
            user.save()
            self.stdout.write(self.style.SUCCESS("Created test user: testuser"))
        else:
            self.stdout.write("Test user already exists, skipping.")

        # Create user profile
        profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "skill_gaps": [
                    "route optimization",
                    "fuel efficiency",
                    "cargo load planning",
                ],
                "quarterly_goals": [
                    "Reduce delivery time by 15%",
                    "Cut fuel costs by 10%",
                    "95% on-time delivery",
                ],
            },
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Created user profile"))

        # Create modules
        modules_data = [
            {
                "name": "Route Optimization Fundamentals",
                "category": "Operations",
                "description": "Learn how to analyze delivery routes, identify bottlenecks, and apply optimization algorithms to reduce transit times and costs.",
            },
            {
                "name": "Warehouse Safety Protocols",
                "category": "Safety",
                "description": "Master essential warehouse safety procedures including hazard identification, PPE requirements, and emergency response protocols.",
            },
            {
                "name": "Fleet GPS & Telematics",
                "category": "Technology",
                "description": "Understand GPS tracking systems, telematics data analysis, and how to leverage real-time fleet data for operational decisions.",
            },
            {
                "name": "Fuel Efficiency Best Practices",
                "category": "Operations",
                "description": "Discover techniques for reducing fuel consumption across your fleet, from driver behavior coaching to vehicle maintenance schedules.",
            },
            {
                "name": "Cargo Loading Optimization",
                "category": "Operations",
                "description": "Learn volumetric loading techniques, weight distribution principles, and how to maximize cargo space utilization safely.",
            },
        ]

        for module_data in modules_data:
            module, created = Module.objects.get_or_create(
                name=module_data["name"],
                defaults={
                    "category": module_data["category"],
                    "description": module_data["description"],
                },
            )
            if created:
                self.stdout.write(f"  Created module: {module.name}")

            # Create progress record for each module
            UserProgress.objects.get_or_create(
                user=user,
                module=module,
                defaults={"status": "not_started"},
            )

        self.stdout.write(self.style.SUCCESS("Seed data loaded successfully!"))
