from import_export import resources, fields
from tracker.models import Transaction, Category
from import_export.widgets import ForeignKeyWidget, DateWidget

class TransactionResource(resources.ModelResource):

    category = fields.Field(
        column_name='category',
        attribute='category',
        widget=ForeignKeyWidget(Category, field='name')
    )

    date = fields.Field(
        column_name='date',
        attribute='date',
        widget=DateWidget(format='%d/%m/%Y')  # Matching the format in your CSV file
    )

    def after_init_instance(self, instance, new, row, **kwargs):
        instance.user = kwargs.get('user')

    def before_import_row(self, row, **kwargs):
        # Skip rows with any critical field missing
        if not row['amount'] or not row['type'] or not row['date'] or not row['category']:
            print(f"Skipping row with missing data: {row}")

    class Meta:
        model = Transaction
        fields = (
            'amount',
            'type',
            'date',
            'category',
        )

        import_id_fields = (
            'amount',
            'type',
            'date',
            'category',
        )