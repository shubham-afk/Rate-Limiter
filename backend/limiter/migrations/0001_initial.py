from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(name="RateLimitRule", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("name", models.CharField(max_length=80)), ("key", models.CharField(max_length=160, unique=True)),
            ("algorithm", models.CharField(choices=[("fixed_window", "Fixed window"), ("sliding_log", "Sliding window log"), ("token_bucket", "Token bucket"), ("sliding_counter", "Sliding window counter")], default="token_bucket", max_length=32)),
            ("limit", models.PositiveIntegerField(default=60)), ("window_seconds", models.PositiveIntegerField(default=60)), ("scope", models.CharField(default="api_key", max_length=16)), ("endpoint", models.CharField(blank=True, max_length=200)), ("tier", models.CharField(default="free", max_length=32)), ("enabled", models.BooleanField(default=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True))]),
        migrations.CreateModel(name="RequestEvent", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("key_label", models.CharField(max_length=160)), ("endpoint", models.CharField(max_length=200)), ("allowed", models.BooleanField()), ("algorithm", models.CharField(max_length=32)), ("latency_ms", models.FloatField(default=0)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("rule", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="events", to="limiter.ratelimitrule"))]),
    ]
