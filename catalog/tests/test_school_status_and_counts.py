"""School.is_active, and the active_orders_count annotation.

Added for the Locations screens (F12) — a lead needs to see and filter on
whether a school is still taking deliveries, and how many orders it has
in flight, neither of which existed on this endpoint before.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tests.factories import build_sites, make_user
from orders.models.school_orders import OrderStatus, SchoolOrder

Role = User.Role


class SchoolIsActiveTests(APITestCase):
    def setUp(self):
        self.sites = build_sites()
        self.lead = make_user("sharon", Role.PROGRAM_LEAD)
        self.client.force_authenticate(self.lead)

    def test_defaults_to_active(self):
        self.assertTrue(self.sites["school_a"].is_active)

    def test_a_lead_can_deactivate_a_school(self):
        url = reverse("catalog:school-detail", args=[self.sites["school_a"].id])
        response = self.client.patch(url, {"is_active": False})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_active"])
        self.sites["school_a"].refresh_from_db()
        self.assertFalse(self.sites["school_a"].is_active)

    def test_filterable_by_is_active(self):
        self.sites["school_b"].is_active = False
        self.sites["school_b"].save(update_fields=["is_active"])

        response = self.client.get(reverse("catalog:school-list"), {"is_active": "true"})

        names = {row["name"] for row in response.data["results"]}
        self.assertIn(self.sites["school_a"].name, names)
        self.assertNotIn(self.sites["school_b"].name, names)


class ActiveOrdersCountTests(APITestCase):
    def setUp(self):
        self.sites = build_sites()
        self.lead = make_user("sharon", Role.PROGRAM_LEAD)
        self.client.force_authenticate(self.lead)

    def _order(self, *, status_value):
        return SchoolOrder.objects.create(
            school=self.sites["school_a"],
            student_name="Test Student",
            order_date="2027-01-15",
            status=status_value,
            created_by=self.lead,
        )

    def test_counts_hold_released_and_picked_only(self):
        self._order(status_value=OrderStatus.HOLD)
        self._order(status_value=OrderStatus.RELEASED)
        self._order(status_value=OrderStatus.PICKED)
        # These two should NOT be counted — done, or withdrawn.
        self._order(status_value=OrderStatus.SHIPPED)
        self._order(status_value=OrderStatus.CANCELLED)

        url = reverse("catalog:school-detail", args=[self.sites["school_a"].id])
        response = self.client.get(url)

        self.assertEqual(response.data["active_orders_count"], 3)

    def test_a_school_with_no_orders_counts_zero_not_null(self):
        url = reverse("catalog:school-detail", args=[self.sites["school_a"].id])
        response = self.client.get(url)

        self.assertEqual(response.data["active_orders_count"], 0)
