from datetime import datetime, timedelta
import pytest
from django.urls import reverse
from tracker.models import Category

@pytest.mark.django_db
def test_total_values_appear_on_list_page(user_transactions, client):
    user = user_transactions[0].user
    client.force_login(user)

    income_total = sum(t.amount for t in user_transactions if t.type == 'income')
    expense_total = sum(t.amount for t in user_transactions if t.type == 'expense')
    net = income_total - expense_total

    response = client.get(reverse('transactions-list'))

    assert response.context['total_income'] == income_total
    assert response.context['total_expense'] == expense_total
    assert response.context['net_income'] == net


@pytest.mark.django_db
def test_transaction_type_i_filter(user_transactions, client):
    user = user_transactions[0].user
    client.force_login(user)

    # income check - simulate user selecting income type
    get_params = {'transaction_type': 'income'}
    response = client.get(reverse('transactions-list'), get_params)

    qs = response.context['filter'].qs

    # expect all transactions to be income
    for transaction in qs:
        assert transaction.type == 'income'


@pytest.mark.django_db
def test_transaction_type_e_filter(user_transactions, client):
    user = user_transactions[0].user
    client.force_login(user)

    # user sends expense type
    get_params = {'transaction_type': 'expense'}
    response = client.get(reverse('transactions-list'), get_params)

    qs = response.context['filter'].qs

    # expect all transactions to be expense
    for transaction in qs:
        assert transaction.type == 'expense'


@pytest.mark.django_db
def test_start_end_date_filter(user_transactions, client):
    user = user_transactions[0].user
    client.force_login(user)

    start_date_cutoff = datetime.now().date() - timedelta(days=120)
    get_params = {'start_date': start_date_cutoff}
    response = client.get(reverse('transactions-list'), get_params)

    qs = response.context['filter'].qs

    for transaction in qs:
        assert transaction.date >= start_date_cutoff

    end_date_cutoff = datetime.now().date() - timedelta(days=20)
    get_params = {'end_date': end_date_cutoff}
    response = client.get(reverse('transactions-list'), get_params)

    qs = response.context['filter'].qs

    for transaction in qs:
        assert transaction.date <= end_date_cutoff


@pytest.mark.django_db
def test_category_filter(user_transactions, client):
    user = user_transactions[0].user
    client.force_login(user)

    # Get the first 2 categories PKs
    category_pks = Category.objects.all()[:2].values_list('pk', flat=True)
    get_params = {'category': category_pks}

    response = client.get(reverse('transactions-list'), get_params)

    qs = response.context['filter'].qs

    for transaction in qs:
        assert transaction.category.pk in category_pks