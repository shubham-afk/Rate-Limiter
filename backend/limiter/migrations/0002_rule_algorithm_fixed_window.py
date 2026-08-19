# Generated manually for the Phase 2 default/enum correction.
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("limiter", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="ratelimitrule",
            name="algorithm",
            field=models.CharField(
                choices=[
                    ("fixed_window", "Fixed window"),
                    ("sliding_window_log", "Sliding window log"),
                    ("token_bucket", "Token bucket"),
                    ("sliding_window_counter", "Sliding window counter"),
                ],
                default="fixed_window",
                max_length=32,
            ),
        )
    ]
