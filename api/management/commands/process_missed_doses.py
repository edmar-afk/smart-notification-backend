from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from api.models import PatientDose, PatientDoseHistory


class Command(BaseCommand):
    help = "Process overdue doses and record missed medicine doses."

    def handle(self, *args, **options):
        now = timezone.now()
        processed = 0

        # Get candidate records. Recheck each record inside a transaction.
        dose_ids = list(
            PatientDose.objects.filter(
                quantity__gt=0,
                time_prescribe__isnull=False,
                interval_started_at__isnull=False,
            ).values_list("id", flat=True)
        )

        for dose_id in dose_ids:
            with transaction.atomic():
                try:
                    dose = (
                        PatientDose.objects
                        .select_for_update()
                        .get(pk=dose_id)
                    )
                except PatientDose.DoesNotExist:
                    continue

                if not dose.quantity or dose.quantity <= 0:
                    continue

                if not dose.time:
                    continue

                # The stored value is an interval in hours.
                try:
                    interval_hours = int(str(dose.time).strip())
                except (TypeError, ValueError):
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipping dose {dose.pk}: invalid time interval."
                        )
                    )
                    continue

                if interval_hours <= 0:
                    continue

                if not dose.interval_started_at:
                    continue

                due_at = dose.interval_started_at + timedelta(
                    hours=interval_hours
                )

                # The interval has not elapsed yet.
                if now < due_at:
                    continue

                # Record one missed dose.
                PatientDoseHistory.objects.create(
                    patient=dose.patient,
                    medicine_name=dose.medicine_name,
                    status="Missed",
                )

                # Reduce the remaining quantity by one.
                dose.quantity = max(0, dose.quantity - 1)

                # Start a fresh interval only if another dose remains.
                if dose.quantity > 0:
                    dose.interval_started_at = now

                dose.save(
                    update_fields=[
                        "quantity",
                        "interval_started_at",
                    ]
                )

                processed += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"Missed: {dose.medicine_name} | "
                        f"Remaining quantity: {dose.quantity}"
                    )
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Finished. Processed {processed} missed dose(s)."
            )
        )