from datetime import time, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Address, CustomerProfile, User
from bookings.models import Booking
from notifications.models import Notification
from providers.models import ProviderAvailability, ProviderProfile
from reviews.models import Review
from services.models import Service, ServiceCategory

DEMO_PASSWORD = "Demo@12345"  # for LOCAL demo accounts only

# (category name, slug, icon, description, [(service, price, description), ...])
CATALOG = [
    ("Vehicle Repair", "vehicle-repair", "bi-car-front-fill",
     "Cars, bikes and scooters: servicing, repairs and breakdown help.",
     [("General Service", 1500, "Full periodic service and checkup"),
      ("Brake Repair", 900, "Brake pad and brake system repair"),
      ("Battery Replacement", 700, "Battery testing and replacement")]),
    ("AC Service", "ac-service", "bi-snow2",
     "Servicing, gas refill and installation for split and window ACs.",
     [("AC General Service", 600, "Cleaning and performance check"),
      ("AC Gas Refill", 2200, "Leak check and gas refill"),
      ("AC Installation", 1800, "New AC installation")]),
    ("Refrigerator Repair", "refrigerator-repair", "bi-thermometer-snow",
     "Cooling problems, compressor and door seal repairs.",
     [("Cooling Problem", 800, "Diagnosis and repair of poor cooling"),
      ("Compressor Repair", 2500, "Compressor check and repair"),
      ("Door Seal Replacement", 600, "Replace worn door gasket")]),
    ("Washing Machine Repair", "washing-machine-repair", "bi-water",
     "Front-load and top-load washing machine repairs.",
     [("Drum Not Spinning", 700, "Motor and belt inspection"),
      ("Water Drain Issue", 500, "Drain pump and pipe repair"),
      ("Machine Installation", 600, "Installation and demo")]),
    ("Electrical Service", "electrical-service", "bi-lightning-charge-fill",
     "Wiring, fittings and safe electrical repairs for your home.",
     [("Wiring Repair", 500, "Fault finding and wiring repair"),
      ("Fan / Light Installation", 300, "Fit new fans and lights"),
      ("Switchboard Repair", 400, "Repair or replace switchboards")]),
    ("Plumbing", "plumbing", "bi-droplet-fill",
     "Leaks, taps, pipes and drainage problems.",
     [("Leak Repair", 400, "Find and fix leaking pipes"),
      ("Tap Installation", 300, "Install or replace taps"),
      ("Drain Unblocking", 600, "Clear blocked drains")]),
    ("Home Appliance Repair", "home-appliance-repair", "bi-house-gear-fill",
     "Microwaves, mixers, water purifiers and other appliances.",
     [("Microwave Repair", 500, "Microwave diagnosis and repair"),
      ("Mixer / Grinder Repair", 350, "Motor and jar repair"),
      ("Water Purifier Service", 600, "Filter change and service")]),
    ("Other Services", "other-services", "bi-three-dots",
     "Small jobs that don't fit the other categories.",
     [("General Handyman Visit", 400, "Small repair and fixing jobs"),
      ("Furniture Assembly", 500, "Assemble flat-pack furniture")]),
]

# (username, first, last, phone, [category slugs], years, city, area,
#  headline, bio, skills, status)
PROVIDERS = [
    ("ravi_kumar", "Ravi", "Kumar", "9000000001", ["vehicle-repair"], 12,
     "Chennai", "Velachery, Guindy", "Two-wheeler and car mechanic",
     "Experienced mechanic handling servicing, brake work and breakdowns for bikes, scooters and cars.",
     "Engine diagnosis, Brake repair, Battery, Servicing", "APPROVED"),
    ("selvam_m", "Selvam", "Murugan", "9000000002", ["ac-service"], 9,
     "Chennai", "Anna Nagar, Kilpauk", "AC installation and repair expert",
     "Specialist in split and window ACs. Gas refill, cleaning and installation done neatly and on time.",
     "AC repair, Gas refill, Installation, Deep cleaning", "APPROVED"),
    ("farhan_ali", "Farhan", "Ali", "9000000003",
     ["refrigerator-repair", "home-appliance-repair"], 7,
     "Chennai", "T. Nagar, Mylapore", "Refrigerator and appliance technician",
     "Fixes cooling issues, compressor faults and kitchen appliances with genuine spare parts.",
     "Refrigerator, Microwave, Water purifier", "APPROVED"),
    ("meena_l", "Meena", "Lakshmi", "9000000004",
     ["washing-machine-repair", "home-appliance-repair"], 6,
     "Chennai", "Adyar, Besant Nagar", "Washing machine specialist",
     "Repairs front-load and top-load machines of all major brands, with clear pricing before work starts.",
     "Washing machine, Motor repair, Drain issues", "APPROVED"),
    ("karthik_r", "Karthik", "Raja", "9000000005", ["electrical-service"], 10,
     "Chennai", "Tambaram, Chromepet", "Licensed electrician",
     "Home wiring, fittings and fault finding with a focus on safety.",
     "Wiring, Switchboards, Fans and lights, Fault finding", "APPROVED"),
    ("joseph_a", "Joseph", "Antony", "9000000006", ["plumbing"], 8,
     "Chennai", "OMR, Sholinganallur", "Plumber for homes and apartments",
     "Leak repair, tap and bathroom fittings and drain clearing, completed cleanly.",
     "Leak repair, Pipe fitting, Drain cleaning", "APPROVED"),
    ("divya_s", "Divya", "Shankar", "9000000007",
     ["home-appliance-repair", "other-services"], 5,
     "Chennai", "Porur, Valasaravakkam", "Home appliance and handyman services",
     "Friendly all-round help for small appliance repairs and household fixing jobs.",
     "Mixer repair, Furniture assembly, Small repairs", "APPROVED"),
    ("anbu_c", "Anbu", "Chezhian", "9000000008", ["vehicle-repair"], 4,
     "Chennai", "Anna Nagar", "Bike and scooter mechanic",
     "Newly joined mechanic for two-wheeler servicing and repairs.",
     "Scooter repair, Chain and brake work", "PENDING"),
]

# (username, first, last, phone, address line, area, pincode)
CUSTOMERS = [
    ("priya_s", "Priya", "Subramanian", "9100000001", "12, Lake View Road", "Velachery", "600042"),
    ("arun_m", "Arun", "Mohan", "9100000002", "45, Gandhi Street", "Anna Nagar", "600040"),
    ("nisha_r", "Nisha", "Ravi", "9100000003", "8, Temple Street", "Adyar", "600020"),
]

# (customer, provider, category slug, service, day offset, time, status,
#  problem, rating, comment)
BOOKINGS = [
    ("priya_s", "ravi_kumar", "vehicle-repair", "General Service", -20, time(10, 0), "COMPLETED",
     "Scooter is due for its periodic service.", 5,
     "Very professional and on time. The scooter runs smoothly now."),
    ("arun_m", "selvam_m", "ac-service", "AC Gas Refill", -15, time(11, 0), "COMPLETED",
     "AC is running but not cooling properly.", 5,
     "Found the leak quickly and fixed it. Fair price."),
    ("nisha_r", "farhan_ali", "refrigerator-repair", "Cooling Problem", -12, time(15, 0), "COMPLETED",
     "Fridge is not cooling and makes noise.", 4,
     "Good work. Arrived a little late but fixed it well."),
    ("priya_s", "meena_l", "washing-machine-repair", "Drum Not Spinning", -10, time(9, 30), "COMPLETED",
     "Drum does not spin during wash.", 5,
     "Explained the problem clearly and repaired it the same day."),
    ("arun_m", "karthik_r", "electrical-service", "Wiring Repair", -8, time(16, 0), "COMPLETED",
     "Frequent tripping of the main switch.", 4,
     "Careful and safe work. Would book again."),
    ("nisha_r", "joseph_a", "plumbing", "Leak Repair", -6, time(12, 0), "COMPLETED",
     "Water leaking under the kitchen sink.", 5,
     "Quick and clean. No mess left behind."),
    ("priya_s", "selvam_m", "ac-service", "AC General Service", -4, time(10, 30), "COMPLETED",
     "Yearly AC cleaning and checkup.", 4,
     "Thorough cleaning and polite behaviour."),
    ("arun_m", "ravi_kumar", "vehicle-repair", "Brake Repair", 2, time(10, 0), "ACCEPTED",
     "Brakes feel weak and make a noise.", None, ""),
    ("nisha_r", "karthik_r", "electrical-service", "Fan / Light Installation", 3, time(14, 0), "REQUESTED",
     "Need two ceiling fans installed.", None, ""),
    ("priya_s", "farhan_ali", "refrigerator-repair", "Door Seal Replacement", 1, time(14, 0), "REQUESTED",
     "Fridge door is not closing fully.", None, ""),
    ("arun_m", "joseph_a", "plumbing", "Tap Installation", -2, time(17, 0), "CANCELLED",
     "Replace bathroom tap.", None, ""),
]


class Command(BaseCommand):
    help = "Fill the database with fictional demo data for development."

    @transaction.atomic
    def handle(self, *args, **options):
        self.create_catalog()
        self.create_providers()
        self.create_customers()
        self.create_bookings()
        self.stdout.write(self.style.SUCCESS("Demo data ready."))
        self.stdout.write(f"All demo users have the password: {DEMO_PASSWORD}")

    def make_user(self, username, first, last, phone, role):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first,
                "last_name": last,
                "email": f"{username}@example.com",
                "phone": phone,
                "role": role,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)  # hashed, never stored as plain text
            user.save()
        return user

    def create_catalog(self):
        for name, slug, icon, desc, services in CATALOG:
            category, _ = ServiceCategory.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "icon": icon, "description": desc},
            )
            for svc_name, price, svc_desc in services:
                Service.objects.get_or_create(
                    category=category,
                    name=svc_name,
                    defaults={"base_price": price, "description": svc_desc},
                )
        self.stdout.write("Categories and services: done")

    def create_providers(self):
        for (username, first, last, phone, slugs, years, city, area,
             headline, bio, skills, status) in PROVIDERS:
            user = self.make_user(username, first, last, phone, User.Role.PROVIDER)
            profile, created = ProviderProfile.objects.get_or_create(
                user=user,
                defaults={
                    "headline": headline,
                    "bio": bio,
                    "experience_years": years,
                    "skills": skills,
                    "city": city,
                    "service_area": area,
                    "verification_status": status,
                },
            )
            if created:
                profile.categories.set(ServiceCategory.objects.filter(slug__in=slugs))
                for weekday in range(6):  # Monday to Saturday
                    ProviderAvailability.objects.create(
                        provider=profile,
                        weekday=weekday,
                        start_time=time(9, 0),
                        end_time=time(18, 0),
                    )
        self.stdout.write("Providers: done")

    def create_customers(self):
        for username, first, last, phone, line1, area, pincode in CUSTOMERS:
            user = self.make_user(username, first, last, phone, User.Role.CUSTOMER)
            CustomerProfile.objects.get_or_create(user=user)
            Address.objects.get_or_create(
                user=user,
                label="Home",
                defaults={
                    "line1": line1,
                    "area": area,
                    "city": "Chennai",
                    "pincode": pincode,
                    "is_default": True,
                },
            )
        self.stdout.write("Customers: done")

    def create_bookings(self):
        if Booking.objects.exists():
            self.stdout.write("Bookings already exist: skipped")
            return

        today = timezone.localdate()
        for (cust, prov, slug, svc_name, offset, when, status,
             problem, rating, comment) in BOOKINGS:
            customer = User.objects.get(username=cust)
            provider = ProviderProfile.objects.get(user__username=prov)
            service = Service.objects.get(category__slug=slug, name=svc_name)
            address = customer.addresses.first().full_address()

            booking = Booking.objects.create(
                customer=customer,
                provider=provider,
                service=service,
                scheduled_date=today + timedelta(days=offset),
                scheduled_time=when,
                address=address,
                problem_description=problem,
                status=status,
                final_price=service.base_price if status == "COMPLETED" else None,
            )

            if status == "COMPLETED" and rating:
                Review.objects.create(booking=booking, rating=rating, comment=comment)
            if status == "REQUESTED":
                Notification.objects.create(
                    user=provider.user,
                    message="You received a new booking request.",
                )
            if status == "ACCEPTED":
                Notification.objects.create(
                    user=customer, message="Your booking has been accepted."
                )
            if status == "COMPLETED":
                Notification.objects.create(
                    user=customer,
                    message="Your booking has been completed. Please leave a review.",
                )
        self.stdout.write("Bookings, reviews and notifications: done")