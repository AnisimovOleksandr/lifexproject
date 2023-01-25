def registration(login, password, name, age, email, card, connection):
    cursor = connection.cursor()
    print(login, password, name, age, email, card, connection)

    cursor.callproc('register_customer', (login, password, name, age, email, card))

    status = cursor.fetchone()[0]
    print(status)

    return status