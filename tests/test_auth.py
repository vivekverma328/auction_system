def test_create_user_and_login(
    client,
    user_factory,
    token_factory
):
    user = user_factory(
        "Vivek",
        "vivek@example.com"
    )

    assert user["name"] == "Vivek"
    assert user["email"] == "vivek@example.com"

    token = token_factory(
        "vivek@example.com"
    )

    assert token is not None


def test_login_with_wrong_password(
    client,
    user_factory
):
    user_factory(
        "Vivek",
        "vivek@example.com"
    )

    response = client.post(
        "/auth/login",
        data={
            "username": "vivek@example.com",
            "password": "WrongPassword"
        }
    )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Incorrect email or password"
    )