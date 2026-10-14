"""
API 文档:Swagger 页面可访问,OpenAPI 文档结构完整(spectree 3.0 生成)。
"""


def test_swagger_page(client):
    rv = client.get("/apidoc/swagger/")
    assert rv.status_code == 200


def test_openapi_document_structure(client):
    rv = client.get("/apidoc/openapi.json")
    assert rv.status_code == 200

    data = rv.get_json()
    assert data["openapi"].startswith("3.")
    assert len(data["paths"]) > 20
    assert "AuthorizationBearer" in data["components"]["securitySchemes"]
    # 登录接口声明了请求体与 200/400 响应
    login_post = data["paths"]["/cms/user/login"]["post"]
    assert "application/json" in login_post["requestBody"]["content"]
    assert {"200", "400"} <= set(login_post["responses"])


def test_openapi_book_list_schema(client):
    rv = client.get("/apidoc/openapi.json")
    assert rv.status_code == 200

    data = rv.get_json()
    schema_ref = data["paths"]["/v1/book"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    schema = data["components"]["schemas"][schema_ref.split("/")[-1]]
    assert schema["type"] == "array"
    assert "$ref" in schema["items"]


def test_openapi_create_book_message_schema(client):
    rv = client.get("/apidoc/openapi.json")
    assert rv.status_code == 200

    data = rv.get_json()
    schema_ref = data["paths"]["/v1/book"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"]
    schema_name = schema_ref.split("/")[-1]
    schema = data["components"]["schemas"][schema_name]
    assert schema_name.startswith("ApiMessageSchema")
    assert set(schema["properties"]) == {"code", "message", "request"}
