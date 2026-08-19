from django.db import migrations, models
import django.db.models.deletion


def migrate_legacy_keys(apps, schema_editor):
    ApiKey = apps.get_model("limiter", "ApiKey")
    Rule = apps.get_model("limiter", "RateLimitRule")
    for rule in Rule.objects.exclude(key=""):
        api_key, _ = ApiKey.objects.get_or_create(
            key=rule.key,
            defaults={"name": rule.name, "tier": rule.tier, "enabled": rule.enabled},
        )
        rule.api_key_id = api_key.id
        rule.save(update_fields=["api_key"])


class Migration(migrations.Migration):
    dependencies = [("limiter", "0002_rule_algorithm_fixed_window")]

    operations = [
        migrations.CreateModel(
            name="ApiKey",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80)),
                ("key", models.CharField(max_length=160, unique=True)),
                ("tier", models.CharField(default="free", max_length=32)),
                ("enabled", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AddField(
            model_name="ratelimitrule",
            name="api_key",
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="rule", to="limiter.apikey"),
        ),
        migrations.RunPython(migrate_legacy_keys, migrations.RunPython.noop),
        migrations.RemoveField(model_name="ratelimitrule", name="key"),
        migrations.RemoveField(model_name="ratelimitrule", name="tier"),
        migrations.CreateModel(
            name="RequestLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key_label", models.CharField(blank=True, max_length=160)),
                ("client_ip", models.GenericIPAddressField(blank=True, null=True)),
                ("endpoint", models.CharField(max_length=200)),
                ("allowed", models.BooleanField()),
                ("algorithm", models.CharField(max_length=32)),
                ("latency_ms", models.FloatField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("rule", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="events", to="limiter.ratelimitrule")),
            ],
        ),
    ]
