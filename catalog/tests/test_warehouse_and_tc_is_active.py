"""Warehouse.is_active and TailoringCenter.is_active.

Same pattern as School.is_active (see test_school_status_and_counts.py) —
added for the Locations screens, which show an Active/Inactive badge on
both card lists.
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User
from accounts.tests.factories import build_sites, make_user

Role = User.Role


class WarehouseIsActiveTests(APITestCase):
    def setUp(self):
        self.sites = build_sites()
        self.lead = make_user("sharon", Role.PROGRAM_LEAD)
        self.client.force_authenticate(self.lead)

    def test_defaults_to_active(self):
        self.assertTrue(self.sites["namayemba"].is_active)

    def test_a_lead_can_deactivate_a_warehouse(self):
        url = reverse("catalog:warehouse-detail", args=[self.sites["namayemba"].id])
        response = self.client.patch(url, {"is_active": False})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_active"])
        self.sites["namayemba"].refresh_from_db()
        self.assertFalse(self.sites["namayemba"].is_active)

    def test_filterable_by_is_active(self):
        self.sites["serere"].is_active = False
        self.sites["serere"].save(update_fields=["is_active"])

        response = self.client.get(reverse("catalog:warehouse-list"), {"is_active": "true"})

        names = {row["name"] for row in response.data["results"]}
        self.assertIn(self.sites["namayemba"].name, names)
        self.assertNotIn(self.sites["serere"].name, names)


class TailoringCenterIsActiveTests(APITestCase):
    def setUp(self):
        self.lead = make_user("sharon", Role.PROGRAM_LEAD)
        self.client.force_authenticate(self.lead)
        from catalog.models import TailoringCenter

        self.idudi = TailoringCenter.objects.create(name="Idudi")
        self.serere_tc = TailoringCenter.objects.create(name="Serere")

    def test_defaults_to_active(self):
        self.assertTrue(self.idudi.is_active)

    def test_a_lead_can_deactivate_a_tailoring_center(self):
        url = reverse("catalog:tailoring-center-detail", args=[self.idudi.id])
        response = self.client.patch(url, {"is_active": False})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_active"])
        self.idudi.refresh_from_db()
        self.assertFalse(self.idudi.is_active)

    def test_filterable_by_is_active(self):
        self.serere_tc.is_active = False
        self.serere_tc.save(update_fields=["is_active"])

        response = self.client.get(
            reverse("catalog:tailoring-center-list"), {"is_active": "true"}
        )

        names = {row["name"] for row in response.data["results"]}
        self.assertIn(self.idudi.name, names)
        self.assertNotIn(self.serere_tc.name, names)
