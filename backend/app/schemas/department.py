from pydantic import BaseModel, Field
from typing import Optional, List


class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=50, description="院系名称")
    code: str = Field(..., max_length=20, description="院系编码")


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None


class Department(DepartmentBase):
    id: int

    class Config:
        from_attributes = True


class DepartmentSimple(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True


class MajorBase(BaseModel):
    name: str = Field(..., max_length=50, description="专业名称")
    code: str = Field(..., max_length=20, description="专业编码")
    department_id: int = Field(..., description="所属院系ID")


class MajorCreate(MajorBase):
    pass


class MajorUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    department_id: Optional[int] = None


class Major(MajorBase):
    id: int

    class Config:
        from_attributes = True


class MajorSimple(BaseModel):
    id: int
    name: str
    code: str
    department_id: int

    class Config:
        from_attributes = True


class DepartmentWithMajors(Department):
    majors: List[MajorSimple] = []

    class Config:
        from_attributes = True
