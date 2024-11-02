mysql -u root -p

CREATE DATABASE hackathon_db;

CREATE USER 'hackathon_user'@'localhost' IDENTIFIED BY 'password123';

GRANT ALL PRIVILEGES ON hackathon_db.\* TO 'hackathon_user'@'localhost';

FLUSH PRIVILEGES;
