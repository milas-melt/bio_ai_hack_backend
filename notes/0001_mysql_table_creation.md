mysql -u hackathon_user -p

USE hackathon_db;

CREATE TABLE items (
id INT AUTO_INCREMENT PRIMARY KEY,
name VARCHAR(255) NOT NULL
);
