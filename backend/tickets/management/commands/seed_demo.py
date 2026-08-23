"""
Seeds the database with realistic demo data for the NetDesk portfolio project.

Usage:
    python manage.py seed_demo                # wipe + seed
    python manage.py seed_demo --keep         # seed without wiping first

Creates:
    - 3 staff (1 admin, 1 manager, 1 agent, 1 technician)
    - 5 customers with profiles
    - 6 categories
    - 3 outages (2 active, 1 resolved)
    - 22 tickets across every status/priority combo
    - Conversation, internal notes, ratings, activity, and notifications
"""
import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from users.models import User, Customer
from tickets.models import (
    TicketCategory, Ticket, TicketComment, InternalNote,
    TicketRating, TicketActivity, Outage,
)
from notifications.models import Notification


CATEGORIES = [
    ("Network Outage",       "No internet or intermittent connectivity"),
    ("Slow Speed",           "Bandwidth below subscribed plan"),
    ("Billing",              "Invoice, payment, or refund queries"),
    ("Installation",         "New setup or relocation"),
    ("Router / Equipment",   "Modem, router, or ONT issues"),
    ("Account & Password",   "Login, portal, or account changes"),
]

STAFF = [
    dict(reg_number="ADM-0001", username="Amos Shehzad",   phone_number="03000000001",
         role="ADMIN",         password="Admin@123",   is_staff=True, is_superuser=True),
    dict(reg_number="MGR-0001", username="Sara Manager",   phone_number="03000000002",
         role="MANAGER",       password="Manager@123", is_staff=True),
    dict(reg_number="AGT-0001", username="Ali Agent",      phone_number="03000000003",
         role="SUPPORT_AGENT", password="Agent@123",   is_staff=True),
    dict(reg_number="TEC-0001", username="Bilal Tech",     phone_number="03000000004",
         role="TECHNICIAN",    password="Tech@123",    is_staff=True),
]

CUSTOMERS = [
    dict(reg_number="CUST-2026-00001", username="Ahmed Raza",    phone_number="03210000001",
         area="Model Town",     package="Fiber 50 Mbps"),
    dict(reg_number="CUST-2026-00002", username="Fatima Khan",   phone_number="03210000002",
         area="DHA Phase 5",    package="Fiber 100 Mbps"),
    dict(reg_number="CUST-2026-00003", username="Usman Malik",   phone_number="03210000003",
         area="Gulberg III",    package="Fiber 25 Mbps"),
    dict(reg_number="CUST-2026-00004", username="Ayesha Iqbal",  phone_number="03210000004",
         area="Bahria Town",    package="Fiber 100 Mbps"),
    dict(reg_number="CUST-2026-00005", username="Hassan Ali",    phone_number="03210000005",
         area="Johar Town",     package="Fiber 50 Mbps"),
]

# Rich, believable ISP tickets. (title, description, category_idx, priority, status, customer_idx, escalated, ai_replies)
TICKETS = [
    # === Model Town outage cluster (Ahmed, Usman) — ties into outage ===
    ("No internet since morning",
     "My internet has been completely down since 8am today. I've tried restarting the router multiple times but no lights come on for the internet indicator. Working from home so this is very urgent.",
     0, "CRITICAL", "ASSIGNED", 0, False, 2),

    ("Connection keeps dropping every 10 minutes",
     "Every ten minutes or so my WiFi drops for about 30 seconds and then reconnects. It's been like this for two days now. Very disruptive during video calls.",
     0, "HIGH", "IN_PROGRESS", 2, False, 3),

    # === Speed complaints ===
    ("Getting 8 Mbps instead of 50",
     "I'm paying for 50 Mbps but speedtest.net shows only 8 Mbps download. This has been the case all week. Please check my line.",
     1, "HIGH", "IN_PROGRESS", 4, False, 2),

    ("Streaming buffering during peak hours",
     "Netflix and YouTube start buffering every evening between 8pm and 11pm. Rest of the day it seems fine. Could this be network congestion?",
     1, "MEDIUM", "OPEN", 1, False, 1),

    # === Billing ===
    ("Extra Rs 500 on this month's bill",
     "This month's bill shows Rs 3,500 instead of the usual Rs 3,000. I haven't upgraded my package. Can you explain the extra charge?",
     2, "MEDIUM", "RESOLVED", 1, False, 1),

    ("Paid last week but still shows due",
     "I paid my bill on August 15 via EasyPaisa (transaction ID: EP2884711) but the portal still shows the bill as unpaid. Please update.",
     2, "MEDIUM", "RESOLVED", 3, False, 2),

    ("Request advance invoice for company reimbursement",
     "I need an advance invoice for next month's bill so I can submit it for reimbursement at my office before the 25th. Is this possible?",
     2, "LOW", "OPEN", 0, False, 1),

    # === Installation ===
    ("Schedule installation at new address",
     "I'm moving to a new house in DHA Phase 6 next week. Please schedule a technician to install my connection there on Saturday morning.",
     3, "MEDIUM", "ASSIGNED", 3, False, 1),

    ("Fiber installation appointment missed",
     "The technician was supposed to come yesterday between 2-5pm for a new installation but nobody showed up. Please reschedule.",
     3, "HIGH", "IN_PROGRESS", 4, True, 3),

    # === Router / Equipment ===
    ("Router LED blinking red",
     "The power light on my router is blinking red instead of solid green. I have tried unplugging and plugging back in but no change. Is the router faulty?",
     4, "HIGH", "OPEN", 2, False, 2),

    ("WiFi signal very weak in bedroom",
     "The router is in the living room and the WiFi signal is very weak in my bedroom (about 12 meters away). Any suggestions for extenders or a better router?",
     4, "LOW", "OPEN", 1, False, 1),

    ("ONT device making buzzing noise",
     "My ONT device has started making a low buzzing noise that has become louder over the last few days. Is this safe or should it be replaced?",
     4, "MEDIUM", "OPEN", 4, False, 1),

    # === Account & Password ===
    ("Cannot log in to customer portal",
     "I forgot my portal password and the reset email is not coming through. I've checked spam folder. Please help.",
     5, "MEDIUM", "RESOLVED", 0, False, 1),

    ("Update phone number on account",
     "I'd like to update the phone number linked to my account. New number is 0322-9876543. Old number is no longer active.",
     5, "LOW", "CLOSED", 2, False, 1),

    # === Resolved with ratings (for the demo dashboard to look alive) ===
    ("Speed dropped after storm",
     "Speeds dropped significantly after last week's storm. Started at 50 Mbps, now getting 15 Mbps. Please check line.",
     1, "HIGH", "CLOSED", 3, False, 2),

    ("Package upgrade request",
     "I'd like to upgrade from Fiber 25 to Fiber 100 Mbps. What's the pricing and how long does it take?",
     2, "LOW", "CLOSED", 2, False, 1),

    ("Internet slow only in evenings",
     "Everything works well during the day but by 9pm, browsing becomes really slow. Speedtest confirms significant drop.",
     1, "MEDIUM", "CLOSED", 1, False, 3),

    ("Router replacement after lightning",
     "My router stopped working after a lightning strike near my house. Need a replacement urgently.",
     4, "CRITICAL", "CLOSED", 4, False, 2),

    # === Escalated tickets ===
    ("Complete service outage in Bahria Town",
     "There's a complete outage in my whole street in Bahria Town for the past 6 hours. Multiple neighbours also affected. This is unacceptable.",
     0, "CRITICAL", "IN_PROGRESS", 3, True, 4),

    ("Repeated billing errors — need supervisor",
     "This is the third month in a row I've been overcharged. I've complained twice and been told it's fixed but it's not. I want to speak to a supervisor.",
     2, "HIGH", "ASSIGNED", 1, True, 3),

    # === Waiting on customer ===
    ("Need photo of router LED status",
     "To diagnose the connection issue, please send a photo showing the LED lights currently on your router.",
     4, "MEDIUM", "WAITING_CUSTOMER", 0, False, 1),

    # === Fresh open, no AI yet ===
    ("Cannot open portal on mobile",
     "The NetDesk portal loads on my laptop but on my phone (Android) the login page just keeps spinning after I click Sign In.",
     5, "LOW", "OPEN", 4, False, 0),
]


class Command(BaseCommand):
    help = "Wipe and seed the database with realistic demo data."

    def add_arguments(self, parser):
        parser.add_argument('--keep', action='store_true',
                            help="Skip wiping existing data before seeding.")

    @transaction.atomic
    def handle(self, *args, **opts):
        if not opts['keep']:
            self.stdout.write(self.style.WARNING("Wiping existing data..."))
            Notification.objects.all().delete()
            TicketActivity.objects.all().delete()
            TicketRating.objects.all().delete()
            InternalNote.objects.all().delete()
            TicketComment.objects.all().delete()
            Ticket.objects.all().delete()
            Outage.objects.all().delete()
            TicketCategory.objects.all().delete()
            Customer.objects.all().delete()
            # Keep superusers; delete only app-created users
            User.objects.filter(is_superuser=False).delete()
            self.stdout.write(self.style.SUCCESS("  Wipe complete."))

        # --- Categories ---
        self.stdout.write("Creating categories...")
        cats = []
        for name, desc in CATEGORIES:
            c, _ = TicketCategory.objects.get_or_create(name=name, defaults={'description': desc})
            cats.append(c)

        # --- Staff ---
        self.stdout.write("Creating staff...")
        staff_users = {}
        for s in STAFF:
            u = User.objects.filter(reg_number=s['reg_number']).first()
            if not u:
                u = User(
                    reg_number=s['reg_number'],
                    username=s['username'],
                    phone_number=s['phone_number'],
                    role=s['role'],
                    is_staff=s.get('is_staff', False),
                    is_superuser=s.get('is_superuser', False),
                    must_change_password=False,
                )
                u.set_password(s['password'])
                u.save()
            staff_users[s['role']] = u

        agent = staff_users['SUPPORT_AGENT']
        technician = staff_users['TECHNICIAN']
        manager = staff_users['MANAGER']
        admin = staff_users['ADMIN']

        # --- Customers ---
        self.stdout.write("Creating customers...")
        customers = []
        for c in CUSTOMERS:
            u = User.objects.filter(reg_number=c['reg_number']).first()
            if not u:
                u = User(
                    reg_number=c['reg_number'],
                    username=c['username'],
                    phone_number=c['phone_number'],
                    role='CUSTOMER',
                    must_change_password=False,
                )
                u.set_password('Customer@123')
                u.save()
            Customer.objects.get_or_create(
                user=u,
                defaults=dict(
                    phone=c['phone_number'],
                    address=f"{c['area']}, Lahore",
                    service_area=c['area'],
                    internet_package=c['package'],
                ),
            )
            customers.append(u)

        # --- Outages ---
        self.stdout.write("Creating outages...")
        Outage.objects.create(
            area="Model Town, Lahore",
            description="Fiber cut on main feeder cable due to road construction. ETA: 6 hours.",
            status="ACTIVE",
            started_at=timezone.now() - timedelta(hours=3),
            created_by=admin,
        )
        Outage.objects.create(
            area="Bahria Town Phase 4, Lahore",
            description="Core switch failure at aggregation point. Field team dispatched.",
            status="ACTIVE",
            started_at=timezone.now() - timedelta(hours=6),
            created_by=manager,
        )
        Outage.objects.create(
            area="DHA Phase 5, Lahore",
            description="Scheduled maintenance completed successfully.",
            status="RESOLVED",
            started_at=timezone.now() - timedelta(days=2, hours=2),
            resolved_at=timezone.now() - timedelta(days=2),
            created_by=admin,
        )

        # --- Tickets ---
        self.stdout.write("Creating tickets, comments, notes, ratings, activities...")
        now = timezone.now()
        for i, t in enumerate(TICKETS):
            title, desc, cat_i, priority, status, cust_i, escalated, ai_replies = t
            created = now - timedelta(hours=random.randint(1, 96))

            ticket = Ticket.objects.create(
                ticket_number=f"TKT-2026-{(i+1):05d}",
                title=title,
                description=desc,
                category=cats[cat_i],
                status=status,
                priority=priority,
                customer=customers[cust_i],
                assigned_agent=agent if status in ("ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED", "WAITING_CUSTOMER") else None,
                assigned_technician=technician if status in ("IN_PROGRESS", "RESOLVED", "CLOSED") and cat_i in (0, 3, 4) else None,
                escalated=escalated,
                ai_reply_count=ai_replies,
            )
            # Bypass auto_now_add to backdate
            Ticket.objects.filter(pk=ticket.pk).update(created_at=created)

            # AI-first comment (if the AI replied)
            if ai_replies > 0:
                TicketComment.objects.create(
                    ticket=ticket, author=admin,  # admin used as bot voice for demo
                    message=self._ai_opening_message(cat_i, priority),
                )

            # Customer follow-up + agent reply on some
            if status in ("IN_PROGRESS", "RESOLVED", "CLOSED", "WAITING_CUSTOMER", "ASSIGNED") and ai_replies > 0:
                TicketComment.objects.create(
                    ticket=ticket, author=customers[cust_i],
                    message="I've already tried that, still not working.",
                )
                TicketComment.objects.create(
                    ticket=ticket, author=agent,
                    message="Understood — I've escalated this to our field team. A technician will contact you shortly." if escalated
                            else "Thanks — I'm checking your line from our end and will update you in a few minutes.",
                )

            # Internal notes for staff coordination
            if status in ("IN_PROGRESS", "ASSIGNED") and cat_i == 0:
                InternalNote.objects.create(
                    ticket=ticket, author=agent,
                    message=f"Multiple tickets from {customers[cust_i].username.split()[0]}'s area today — probably the Model Town outage. Group under OUT-2026-01.",
                )
            if escalated:
                InternalNote.objects.create(
                    ticket=ticket, author=manager,
                    message="Escalated by AI — customer is frustrated. Handle personally, waive next month's bill if possible.",
                )

            # Ratings for closed tickets
            if status == "CLOSED":
                TicketRating.objects.create(
                    ticket=ticket,
                    score=random.choice([4, 4, 5, 5, 5, 3]),
                    feedback=random.choice([
                        "Quick response, issue solved.",
                        "Very helpful support team.",
                        "Took a bit long but resolved.",
                        "Excellent service, thank you.",
                        "",
                    ]),
                )
                Ticket.objects.filter(pk=ticket.pk).update(
                    closed_at=now - timedelta(hours=random.randint(1, 24)),
                    resolved_at=now - timedelta(hours=random.randint(2, 30)),
                )

            # Activity log
            TicketActivity.objects.create(
                ticket=ticket, actor=customers[cust_i],
                action="created", details=f"Ticket created: {title}",
            )
            if ai_replies > 0:
                TicketActivity.objects.create(
                    ticket=ticket, actor=admin,
                    action="ai_analyzed",
                    details=f"Category: {cats[cat_i].name}, Priority: {priority}, Confidence: 0.87",
                )
            if status != "OPEN":
                TicketActivity.objects.create(
                    ticket=ticket, actor=agent,
                    action="assigned", details=f"Assigned to {agent.username}",
                )
            if escalated:
                TicketActivity.objects.create(
                    ticket=ticket, actor=admin,
                    action="escalated", details="AI escalated due to repeated failed troubleshooting",
                )
            if status == "CLOSED":
                TicketActivity.objects.create(
                    ticket=ticket, actor=agent,
                    action="closed", details="Ticket resolved and closed",
                )

        # --- Notifications for a couple of users ---
        self.stdout.write("Creating notifications...")
        for u in [admin, agent, manager]:
            Notification.objects.create(recipient=u, message="New critical ticket: Model Town outage")
            Notification.objects.create(recipient=u, message="Bahria Town outage escalated by AI")
        Notification.objects.create(recipient=customers[0], message="Your ticket TKT has an update from support")

        # --- Summary ---
        self.stdout.write(self.style.SUCCESS("\n=== Seed complete ==="))
        self.stdout.write(f"  Staff:         {User.objects.filter(role__in=['ADMIN','MANAGER','SUPPORT_AGENT','TECHNICIAN']).count()}")
        self.stdout.write(f"  Customers:     {User.objects.filter(role='CUSTOMER').count()}")
        self.stdout.write(f"  Tickets:       {Ticket.objects.count()}")
        self.stdout.write(f"  Comments:      {TicketComment.objects.count()}")
        self.stdout.write(f"  Internal notes:{InternalNote.objects.count()}")
        self.stdout.write(f"  Ratings:       {TicketRating.objects.count()}")
        self.stdout.write(f"  Outages:       {Outage.objects.count()}")
        self.stdout.write("\nDemo logins (all customers use password 'Customer@123'):")
        self.stdout.write("  ADMIN     ADM-0001  / Admin@123")
        self.stdout.write("  MANAGER   MGR-0001  / Manager@123")
        self.stdout.write("  AGENT     AGT-0001  / Agent@123")
        self.stdout.write("  TECH      TEC-0001  / Tech@123")
        self.stdout.write("  CUSTOMER  CUST-2026-00001  / Customer@123")

    # ------- helpers -------

    def _ai_opening_message(self, cat_i, priority):
        openings = [
            "Hi, I'm sorry you're experiencing connectivity issues. I checked our system and there's an active outage reported in your area. Our field team is working on it and estimated restoration is within a few hours. I'll keep you updated.",
            "Thanks for reaching out about the slow speeds. I ran a quick check on your line and I'll walk you through a few steps: 1) Restart your router, 2) Try a wired connection to rule out WiFi, 3) Run a speedtest at speedtest.net. Let me know the results and I'll take it from there.",
            "Thanks for the message. I've pulled up your billing history. Let me review the charges and get back to you within a few minutes with a full breakdown.",
            "Thanks for the request. I've flagged this for our installation team. They typically confirm appointments within 24 hours via SMS. If you don't hear back, reply here and I'll follow up personally.",
            "Thanks for the details. Based on what you've described, this sounds like a hardware issue. Let's rule out a few things first, could you unplug the router for 30 seconds, then plug it back in and let me know which lights turn on?",
            "Thanks for reaching out. I can help with that. For security, I'll need to verify your identity, could you confirm your registered phone number on file?",
        ]
        if 0 <= cat_i < len(openings):
            return openings[cat_i]
        return "Thanks for contacting NetDesk. Let me look into this for you."