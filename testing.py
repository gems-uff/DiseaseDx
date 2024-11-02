from typing import List, Optional
from sqlalchemy import ForeignKey, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, Session

class Base(DeclarativeBase):
    pass

class Doenca(Base):
    __tablename__ = "doenca"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, )
    name: Mapped[str] = mapped_column(String(30))

    def __repr__(self) -> str: # Not necessary, but useful for debugging
        return f"Doenca(id={self.id!r}, name={self.name!r})"

# Testing object creation like OOP
fmf = Doenca(name="Familial Mediterranean Fever")

print(fmf)
print(fmf.id)
print(fmf.name)

diabetes = Doenca()
diabetes.name = "Diabetes Melitus"

print(diabetes)
print(diabetes.id)
print(diabetes.name)

# Create a SQLite database in memory
engine = create_engine("sqlite://", echo=True)

# Create the table
Base.metadata.create_all(engine)

# Begin a session to insert data in the database
with Session(engine) as session:
    diabetes = Doenca(
        name="Diabetes Mellitus"
    )

    fmf = Doenca(
        name="Familial Mediterranean Fever"
    )

    session.add_all([diabetes, fmf])
    session.commit()

# Simple select query
session = Session(engine)
select_stmt = select(Doenca) # can use select().join().where().where() etc | select(Doenca).where(Doenca.name == "Familial Mediterranean Fever")

# Session.scalars executes the query and returns the result as a scalar
for doenca in session.scalars(select_stmt):
    print(f"\n{doenca}")
print("")

# Update query
stmt = select(Doenca).where(Doenca.name == "Diabetes Mellitus")
diabetes = session.scalars(stmt).one()

# Update the name of the disease
diabetes.name = "Diabetes Type 2"
session.commit()

# Verify the update
for doenca in session.scalars(select_stmt):
    print(f"\n{doenca}")
print("")

# Delete query
# If I had a class User and a class Address, and User have an Address column, I could delete the address of a user and the address would also be deleted from its own table (cascade)
# I would do a user.address.remove(user_address) and then session.commit(), or if I want to only remove the specific object, I could do:
session.delete(diabetes)

# Commit the deletion
session.commit()

# Verify the deletion
for doenca in session.scalars(select_stmt):
    print(f"\n{doenca}")
print("")

# Close the session
session.close()

# End of quickstart