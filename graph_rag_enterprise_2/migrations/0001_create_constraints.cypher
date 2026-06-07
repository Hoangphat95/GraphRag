// Example migration: create uniqueness constraint for Tire id
CREATE CONSTRAINT IF NOT EXISTS FOR (t:Tire) REQUIRE t.id IS UNIQUE;
