import pytest
from tracker.factories import TransactionFactory, UserFactory


@pytest.fixture
def transactions():
    return TransactionFactory.create_batch(20)

@pytest.fixture
def user_transactions():
    user = UserFactory()
    return TransactionFactory.create_batch(20, user=user)

@pytest.fixture
def new_user():
    return UserFactory()

@pytest.fixture
def transaction_dict_params(new_user):
    transaction = TransactionFactory.create(user=new_user)
    return {
        'type': transaction.type,
        'category': transaction.category_id,
        'date': transaction.date,
        'amount': transaction.amount,
    }