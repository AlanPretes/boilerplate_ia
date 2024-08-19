# Ia

### Env
```
AUTH_TOKEN="token-secreto"
BASIC_AUTH_USERNAME="admin"
BASIC_AUTH_PASSWORD="admin"
SQLALCHEMY_DATABASE_URI="sqlite:///test.db"
```

### Endpoints
```
Endpoint                    Métodos    Path            Descrição       
--------------------------  ---------  --------------  ---------------
api_router.autovist         POST       /api/autovist   API - Consulta por meio do worker Autovist       
api_router.create_log       POST       /api/           API - Nova consulta       
front_router.index          GET        /               Front - Listagem       
front_router.new            GET, POST  /new/           Front - Nova consulta
front_router.get_precision  GET        /precision      Front - Precisão             
```