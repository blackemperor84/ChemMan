-- PostgreSQL Database Setup for Chem-Man Application
-- Run this script as postgres superuser

-- Create database
CREATE DATABASE chemman_dev;

-- Create user
CREATE USER chemman_user WITH PASSWORD 'chemman_pass123';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE chemman_dev TO chemman_user;

-- Connect to the database
\c chemman_dev

-- Grant schema privileges (PostgreSQL 15+)
GRANT ALL ON SCHEMA public TO chemman_user;

-- Grant default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO chemman_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO chemman_user;
