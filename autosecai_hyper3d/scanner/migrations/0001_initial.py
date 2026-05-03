# Generated for the AutoSecAI prototype.

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Scan",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("language", models.CharField(default="auto", max_length=48)),
                ("code_sha256", models.CharField(max_length=64)),
                ("issue_count", models.PositiveIntegerField(default=0)),
                ("risk_score", models.PositiveIntegerField(default=0)),
                ("scan_time_ms", models.FloatField(default=0)),
                (
                    "engine_name",
                    models.CharField(default="AutoSecAI Heuristic Scanner", max_length=120),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Finding",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("external_id", models.CharField(max_length=32)),
                ("type", models.CharField(max_length=120)),
                ("severity", models.CharField(max_length=24)),
                ("cwe", models.CharField(max_length=32)),
                ("owasp", models.CharField(max_length=120)),
                ("line", models.PositiveIntegerField(default=1)),
                ("vulnerable_snippet", models.TextField(blank=True)),
                ("explanation", models.TextField()),
                ("fix", models.TextField()),
                ("secure_example", models.TextField(blank=True)),
                ("confidence", models.CharField(default="Pattern Match", max_length=48)),
                ("learning", models.TextField(blank=True)),
                (
                    "scan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="findings",
                        to="scanner.scan",
                    ),
                ),
            ],
            options={
                "ordering": ["scan", "line", "severity"],
            },
        ),
    ]

