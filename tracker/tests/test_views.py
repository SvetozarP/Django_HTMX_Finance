from datetime import datetime, timedelta
import pytest
from django.db import transaction
from django.urls import reverse
from tracker.models import Category, Transaction
from pytest_django.asserts import assertTemplateUsed


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


@pytest.mark.django_db
def test_add_transaction_request(new_user, transaction_dict_params, client):
    client.force_login(new_user)
    user_transaction_count = Transaction.objects.filter(user=new_user).count()

    # send request with transaction data
    headers = {'HTTP_HX-Request': 'true'}
    response = client.post(
        reverse('create-transaction'),
        transaction_dict_params,
        **headers
    )
    # assert the count has increased after the post request
    assert Transaction.objects.filter(user=new_user).count() == user_transaction_count + 1
    assertTemplateUsed(response, 'tracker/partials/transaction-success.html')


@pytest.mark.django_db
def test_cannot_add_transaction_with_negative_amount(new_user, transaction_dict_params, client):
    client.force_login(new_user)
    user_transaction_count = Transaction.objects.filter(user=new_user).count()

    transaction_dict_params['amount'] = -44

    # send request with transaction data
    headers = {'HTTP_HX-Request': 'true'}
    response = client.post(
        reverse('create-transaction'),
        transaction_dict_params,
        **headers
    )
    # assert the count has increased after the post request
    assert Transaction.objects.filter(user=new_user).count() == user_transaction_count
    assertTemplateUsed(response, 'tracker/partials/create-transaction.html')
    assert 'HX-retarget' in response.headers


@pytest.mark.django_db
def test_update_transaction_request(new_user, transaction_dict_params, client):
    client.force_login(new_user)
    assert Transaction.objects.filter(user=new_user).count() == 1

    transaction = Transaction.objects.first()
    # Update transaction via a POST request - mutate the dict params

    transaction_dict_params['amount'] = 40
    transaction_dict_params['date'] = datetime.now().date()

    client.post(
        reverse('update-transaction', kwargs = {'pk': transaction.pk}),
        transaction_dict_params
    )

    # check the request has UPDATED the data

    assert Transaction.objects.filter(user=new_user).count() == 1

    transaction = Transaction.objects.first()

    assert transaction.amount == 40
    assert transaction.date == datetime.now().date()


@pytest.mark.django_db
def test_delete_transaction_request(new_user, transaction_dict_params, client):
    client.force_login(new_user)
    assert Transaction.objects.filter(user=new_user).count() == 1
    transaction_to_delete = Transaction.objects.first()
    # send DELETE request
    client.delete(
        reverse('delete-transaction', kwargs = {'pk': transaction_to_delete.pk})
    )

    assert Transaction.objects.filter(user=new_user).count() == 0

