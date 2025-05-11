from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.conf import settings
from tracker.forms import TransactionForm
from tracker.models import Transaction
from tracker.filters import TransactionFilter
from django_htmx.http import retarget
from tracker.charting import plot_income_expense_bar_chart, plot_category_pie_chart
from tracker.resources import TransactionResource
from django.http import HttpResponse
from tablib import Dataset

# Create your views here.
def index(request):
    return render(request, 'tracker/index.html')


@login_required
def transactions_list(request):
    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user).select_related('category')
    )

    paginator = Paginator(transaction_filter.qs, settings.PAGE_SIZE)
    transaction_page = paginator.page(1) #default as one when view is triggered

    total_income = transaction_filter.qs.get_total_income()
    total_expense = transaction_filter.qs.get_total_expenses()

    context = {
        'transactions': transaction_page,
        'filter': transaction_filter,
        'total_income': total_income,
        'total_expense': total_expense,
        'net_income': total_income - total_expense,
    }

    if request.htmx:
        return render(request, 'tracker/partials/transactions-container.html', context)

    return render(request, 'tracker/transaction-list.html', context)

@login_required
def create_transaction(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.user = request.user
            transaction.save()
            context = {'message': 'Transaction created successfully'}
            return render(request, 'tracker/partials/transaction-success.html', context)
        else:
            context = {'form': form}
            response = render(request, 'tracker/partials/create-transaction.html', context)
            return retarget(response, "#transaction-block")

    context={'form': TransactionForm()}
    return render(request, 'tracker/partials/create-transaction.html', context)


@login_required
def update_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        if form.is_valid():
            form.save()
            context = {'message': 'Transaction updated successfully'}
            return render(request, 'tracker/partials/transaction-success.html', context)
        else:
            context = {
                'form': form,
                'transaction': transaction,
            }
            response = render(request, 'tracker/partials/update-transaction.html', context)
            return retarget(response, "#transaction-block")

    context = {
        'form': TransactionForm(instance=transaction),
        'transaction': transaction,
    }

    return render(request, 'tracker/partials/update-transaction.html', context)


@login_required
@require_http_methods(['DELETE'])
def delete_transaction(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    transaction.delete()
    context = {
        'message': f'Transaction of {transaction.amount} on {transaction.date} deleted successfully!',
        'delt': 'true',
    }
    return render(request, 'tracker/partials/transaction-success.html', context)


@login_required
def get_transactions(request):
    # import time
    # time.sleep(2)
    page = request.GET.get('page', 1) # default page 1 if no page defined
    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user).select_related('category')
    )

    paginator = Paginator(transaction_filter.qs, settings.PAGE_SIZE)
    context = {
        'transactions': paginator.page(page)
    }
    return render(
        request,
        'tracker/partials/transactions-container.html#transaction_list',
        context
    )

@login_required
def transaction_charts(request):
    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user).select_related('category')
    )
    income_expense_bar = plot_income_expense_bar_chart(transaction_filter.qs)
    category_income_pie = plot_category_pie_chart(
        transaction_filter.qs.filter(type='income'),
    )
    category_expense_pie = plot_category_pie_chart(
        transaction_filter.qs.filter(type='expense'),
    )
    context = {
        'filter': transaction_filter,
        'income_expense_barchart': income_expense_bar.to_html(),
        'category_income_pie': category_income_pie.to_html(),
        'category_expense_pie': category_expense_pie.to_html(),
    }
    if request.htmx:
        return render(request, 'tracker/partials/charts-container.html', context)
    return render(request, 'tracker/charts.html', context)


@login_required
def export(request):

    if request.htmx:
        return HttpResponse(headers={'HX-Redirect': request.get_full_path()})

    transaction_filter = TransactionFilter(
        request.GET,
        queryset=Transaction.objects.filter(user=request.user).select_related('category')
    )

    data = TransactionResource().export(transaction_filter.qs)
    response = HttpResponse(data.csv, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
    return response


# @login_required
# def import_transactions(request):
#     if request.method == 'POST':
#         file = request.FILES.get('file')
#         resource = TransactionResource()
#         dataset = Dataset()
#         dataset.load(file.read().decode(), format='csv')
#         result = resource.import_data(dataset, user=request.user, dry_run=True)
#
#         if not result.has_errors():
#             resource.import_data(dataset, user=request.user, dry_run=False)
#             context = {'message': f'{len(dataset)} transactions imported successfully!'}
#         else:
#             for row in result:
#                 for error in row.errors:
#                     print(error)
#             context = {'message': 'An error occurred'}
#         return render(request, 'tracker/partials/transaction-success.html', context)
#
#     return render(request, 'tracker/partials/import-transactions.html')


def import_transactions(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        resource = TransactionResource()
        dataset = Dataset()
        dataset.load(file.read().decode(), format='csv')

        skipped_rows = []  # To track skipped rows
        valid_data = Dataset(headers=dataset.headers)  # Valid rows to import

        # Iterate through rows to filter out invalid ones
        for i, row in enumerate(dataset.dict):
            if not row['amount'] or not row['type'] or not row['date'] or not row['category']:
                skipped_rows.append((i + 1, row))  # Record skipped row (row number, data)
                continue

            valid_data.append(list(row.values()))  # Add valid row to import data

        # Perform dry run with valid data
        result = resource.import_data(valid_data, user=request.user, dry_run=True)

        if not result.has_errors():
            resource.import_data(valid_data, user=request.user, dry_run=False)
            context = {
                'message': f'{len(valid_data)} transactions imported successfully!',
                'skipped_rows': skipped_rows
            }
        else:
            context = {'message': 'An error occurred during import.', 'errors': result.row_errors()}

        return render(request, 'tracker/partials/transaction-success.html', context)

    return render(request, 'tracker/partials/import-transactions.html')