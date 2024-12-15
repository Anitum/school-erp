# School ERP System

A comprehensive School Enterprise Resource Planning (ERP) system built with Flask, providing tools for managing school operations, student records, and administrative tasks. Developed by Anitum, featuring integration with our cutting-edge Walk-In Attendance System.

## Features

- Student Management
- Course Management
- Staff Management
- Administrative Tools
- Database Integration with SQLAlchemy

## Tech Stack

- **Backend Framework**: Flask 2.3.3
- **Database**: SQLite with SQLAlchemy
- **Frontend**: HTML/CSS/JavaScript with Jinja2 Templates
- **Form Handling**: WTForms
- **Authentication**: Flask-Login (built-in)

## Prerequisites

- Python 3+
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/viralka/school-erp
   cd school-erp
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate 
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with necessary configurations.

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

## Running the Application

1. Start the development server:
   ```bash
   python run.py
   ```

2. Access the application at `http://localhost:5000`

## Project Structure

```
school-erp/
├── app/                    # Main application package
│   ├── models/ # Database models
│   ├── routes/ # Route handlers
│   ├── templates/ # HTML templates
│   └── utils.py # Utility functions
├── migrations/            # Database migrations
├── venv/                  # Virtual environment
├── config.py             # Configuration settings
├── requirements.txt      # Project dependencies
├── run.py               # Application entry point
└── school.db            # SQLite database
```

## API Routes

### Main Routes
- `/` - Dashboard with system statistics

### Authentication Routes (`/auth`)
- `/login` - User login
- `/logout` - User logout
- `/register` - New user registration

### Student Management (`/student`)
- `/student/list` - View all students
- `/student/add` - Add new student
- `/student/<id>` - View student details
- `/student/<id>/edit` - Edit student information
- `/student/<id>/delete` - Delete student record

### Staff Management (`/staff`)
- `/staff/list` - View all staff members
- `/staff/add` - Add new staff member
- `/staff/<id>` - View staff details
- `/staff/<id>/edit` - Edit staff information
- `/staff/<id>/delete` - Delete staff record

### Class Management (`/classes`)
- `/classes/list` - View all classes
- `/classes/add` - Add new class
- `/classes/<id>` - View class details
- `/classes/<id>/edit` - Edit class information
- `/classes/<id>/students` - View students in a class

### Attendance Management (`/attendance`)
- `/attendance/mark` - Mark daily attendance
- `/attendance/view` - View attendance records
- `/attendance/report` - Generate attendance reports

### Fee Management (`/fees`)
- `/fees/collect` - Collect student fees
- `/fees/pending` - View pending fees
- `/fees/history` - View fee collection history
- `/fees/report` - Generate fee reports

### Events Management (`/events`)
- `/events/list` - View all events
- `/events/add` - Add new event
- `/events/calendar` - View events calendar

### Inventory Management (`/inventory`)
- `/inventory/list` - View inventory items
- `/inventory/add` - Add new items
- `/inventory/track` - Track inventory usage

### Branch Management (`/branch`)
- `/branch/list` - View all branches
- `/branch/add` - Add new branch
- `/branch/<id>` - View branch details
- `/branch/<id>/edit` - Edit branch information

Each route supports appropriate HTTP methods (GET, POST, PUT, DELETE) based on its functionality. All routes require proper authentication and authorization based on user roles.

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## About Anitum

Anitum is a startup revolutionizing educational technology with innovative solutions like:

### Walk-In Attendance System
- Seamless walk-in face detection - no manual scanning required
- Ultra-fast attendance marking (1/3 second processing)
- Multi-face scanning capability
- Easy integration with existing systems
- Real-time attendance tracking

For more information about Anitum's products and services, please contact us or visit our website.

## License

This software is proprietary and confidential. Copyright © 2023 Anitum. All rights reserved.

This software and its documentation are protected by copyright law and international treaties. Unauthorized reproduction or distribution of this software, or any portion of it, may result in severe civil and criminal penalties, and will be prosecuted to the maximum extent possible under law.