from requests import get, post, put, delete

# тесты для получения users

print(post('http://127.0.0.1:8080/api/v2/users', json={
    'api_key': 'o2o_secret_api_key',
    'username': 'o3o',
    'email': 'o3o@example.com',
    'hashed_password': '1234',
    'access_level': 1
}).json())
print(get('http://127.0.0.1:8080/api/v2/users',
      json={'api_key': 'o2o_secret_api_key'}).json())


print(post('http://127.0.0.1:8080/api/v2/users', json={
    'api_key': 'o2o_secret_api_key',
    'username': 'o4o',
    'email': 'o4o@example.com',
    'hashed_password': '1234',
    'access_level': 1
}).json())

print(put('http://127.0.0.1:8080/api/v2/users/3', json={
    'api_key': 'o2o_secret_api_key',
    'username': 'o3o',
    'email': 'o3o@example.com',
    'hashed_password': '12345',
    'access_level': 2
}).json())


print(get('http://127.0.0.1:8080/api/v2/users/3',
      json={'api_key': 'o2o_secret_api_key'}).json())

print(delete('http://127.0.0.1:8080/api/v2/users/4',
      json={'api_key': 'o2o_secret_api_key'}).json())

print(get('http://127.0.0.1:8080/api/v2/users',
      json={'api_key': 'o2o_secret_api_key'}).json())


# тесты ссылок на бд

print(post('http://127.0.0.1:5000/api/v2/links', json={
    'api_key': 'o2o_secret_api_key',
    'database_name': 'testDB',
    'sourse_link': 'https://testDB.ru',
    'db_link': 'https://testDBCloud.ru'
}).json())

print(get('http://127.0.0.1:5000/api/v2/links',
      json={'api_key': 'o2o_secret_api_key'}).json())
print(get('http://127.0.0.1:5000/api/v2/links/2',
      json={'api_key': 'o2o_secret_api_key'}).json())

print(put('http://127.0.0.1:5000/api/v2/links/3', json={
    'api_key': 'o2o_secret_api_key',
    'database_name': 'testDB',
    'sourse_link': 'https://testDB.ru',
    'db_link': 'https://testDBCloud.ru'
}).json())


print(delete('http://127.0.0.1:5000/api/v2/links/4',
      json={'api_key': 'o2o_secret_api_key'}).json())

print(get('http://127.0.0.1:5000/api/v2/links',
      json={'api_key': 'o2o_secret_api_key'}).json())

# тест для получения всех баз данных

print(get('http://127.0.0.1:5000/api/v2/databases',
      json={'api_key': 'o2o_secret_api_key'}).json())
