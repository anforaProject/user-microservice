# starlette inports 
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.schemas import SchemaGenerator
import uvicorn


# db imports 

from db import User, UserProfile
from init_db import register_tortoise
import tortoise.exceptions

# custom import 

from errors import DoesNoExist, ValidationError, UserAlreadyExists
from utils import validate_user_creation

app = Starlette(debug=True)

register_tortoise(
    app, db_url="sqlite://memory.sql", modules={"models": ["db"]}, generate_schemas=True
)


schemas = SchemaGenerator(
    {"openapi": "3.0.0", "info": {"title": "Example API", "version": "1.0"}}
)

@app.route('/v1/health', methods=["GET"])
async def homepage(request):
    return JSONResponse({'status': 'running'})

@app.route('/mock')
async def moch(request):
    await User.create(
        username='anforaUser',
        password='shouldBeAHashedPassword',
        email='random@example.com'
    )

    user = await User.get(username='anforaUser')

    prof = UserProfile(
        user_id = user.id
    )

    await prof.save()

    profile = await UserProfile.all()
    prof = await profile[0].to_json()
    print(prof)
    return JSONResponse(prof)

@app.route('/v1/users/{username}', methods=["GET"])
async def get_user_by_username(request):
    username = request.path_params['username']
    try:
        user = await UserProfile.get(user__username=username)
        return JSONResponse(await user.to_json())
    except tortoise.exceptions.DoesNotExist: 
        return DoesNoExist()

@app.route('/v1/activitypub/{username}')
async def get_ap_by_username(request):
    username = request.path_params['username']
    try:
        user = await UserProfile.get(user__username=username)
        print(await user.to_activitystream())
        return JSONResponse(await user.to_activitystream())
    except tortoise.exceptions.DoesNotExist: 
        return DoesNoExist()

@app.route("/schema", methods=["GET"], include_in_schema=False)
def openapi_schema(request):
    return schemas.OpenAPIResponse(request=request)

@app.route('/v1/users/create', methods=['POST'])
async def create_new_user(request):
    
    body = await request.json()
    
    valid = validate_user_creation_request(body)

    if valid:

        # Check that an user with this userma doesn't exists already

        user = await User.get(username=data['username'])
        if user:
            return UserAlreadyExists()

        await User.create(
            username=body['username'],
            password='shouldBeAHashedPassword',
            email='random@example.com'
        )
        
    
    return ValidationError()