import pytest
from django.urls import reverse

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
