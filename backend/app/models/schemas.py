from pydantic import BaseModel,EmailStr,Field
from typing import Literal
class RegisterIn(BaseModel): email:EmailStr; password:str=Field(min_length=8,max_length=128); display_name:str=Field(min_length=2,max_length=60)
class LoginIn(BaseModel): email:EmailStr; password:str
class GenerationIn(BaseModel): kind:Literal['text','speech','image']; prompt:str=Field(min_length=1,max_length=5000); language:Literal['en-NG','pcm','yo','ig','ha','en']='en-NG'
class FeedbackIn(BaseModel): generation_id:str|None=None; rating:int=Field(ge=1,le=5); comment:str=Field(default='',max_length=2000)
class ConsentIn(BaseModel): platform_use:bool=False; evaluation:bool=False; model_training:bool=False; consent_version:str='v1'
