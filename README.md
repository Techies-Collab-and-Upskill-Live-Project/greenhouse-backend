# FYSI Marketplace Backend

Welcome to the FYSI Marketplace backend project! This repository contains the Django-based RESTful API for our eco-friendly e-commerce platform. This README will guide you through setting up your development environment and contributing to the project.

## Table of Contents

- [Project Overview](#project-overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Development Setup](#local-development-setup)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Deployment](#deployment)
- [Team Communication](#team-communication)

## Project Overview

Our backend provides the following core functionalities:

- User Management (customers, vendors, admins)
- Product Management
- Vendor Dashboard
- Customer Features (browsing, cart, checkout)
- Admin Dashboard
<!-- - Eco-Certification System -->
- Payment Processing (Paystack integration)
- Order Fulfillment

## Getting Started

### Prerequisites

Ensure you have the following installed:

- Python 3.8+ (preferably 3.9) with pip

### Local Development Setup

1. Clone the repository:
   ```
   git clone https://github.com/Techies-Collab-and-Upskill-Live-Project/greenhouse-backend.git
   cd greenhouse-backend
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   on macOS use source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your local database:
   <!-- - Create a PostgreSQL database for the project -->
   - We are still going to be using SQLite for development purposes.
   - Copy `.env.example` to `.env` and update the database credentials

5. Apply migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Run the development server:
   ```
   python manage.py runserver
   ```

<!-- The API should now be accessible at `http://localhost:8000/api/`. -->

## Project Structure

(This will be added later)

## Development Workflow

1. Create a new branch for each feature or bug fix:
   ```
   git checkout -b your-feature-name
   ```

2. Make your changes, commit them with clear messages:
   ```
   git commit -m "Add user registration endpoint"
   ```

3. Push your branch and create a pull request on GitHub
4. I will review your pr and merge if there is no conflict
5. Once merged, pull the latest changes and test your feature
6. If there are any issues, create a new branch and fix them
7. Repeat the process until your feature is complete

** Please make sure your branch is always up  to date with the latest changes before you push your content to avoid conflict. **

## Coding Standards

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) for Python code style
- Use meaningful variable and function names
- Write docstrings for all functions, classes, and modules
- Keep functions small and focused on a single task

## Testing

- Write unit tests for all new features and bug fixes
- Run tests before pushing your changes:
  ```
  python manage.py test
  ```

## Deployment

(This will be discussed later)

## Team Communication

- We use Slack for daily communication
- Team meetings are held every Monday and Thursday
- Use GitHub Issues for task tracking and discussions
- Update the project board on GitHub with your progress

## Various Endpoints
- Users/register - Post method
- Users/login ==> Post method
- Users/activate  ==> Post method
- Users/reset-password-request ==> Post method
- Users/reset-pasword ==> Post method   
- Users/change-password ==> Put method
- Users/customer-profile/:userid ==> Put method and Get method
- Users/vendor-profile/:userid ==> Put method and Get method

Remember to keep this README updated as the project evolves. If you have any questions or need help, don't hesitate to reach out to me or post on the Devs WhatsApp group. Let's build an amazing project together! :smile: :rocket: :fire:

Happy coding!