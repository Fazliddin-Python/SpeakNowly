# FastAPI Project Documentation

This project is a FastAPI application structured to provide various APIs for mobile, dashboard, and client site functionalities. 

## Project Structure

- **app/**: Main application package.
  - **api/**: Contains all API-related code.
    - **mobile/**: Mobile API endpoints.
      - **v1/**: Version 1 of the mobile API.
      - **v2/**: Version 2 of the mobile API (to be implemented).
    - **dashboard/**: Dashboard API endpoints.
      - **v1/**: Version 1 of the dashboard API.
      - **v2/**: Version 2 of the dashboard API (to be implemented).
    - **client_site/**: Client site API endpoints.
      - **v1/**: Version 1 of the client site API.
      - **v2/**: Version 2 of the client site API (to be implemented).
  - **models/**: Contains data models used in the application.
  - **services/**: Contains business logic and service layer code.
  - **exceptions/**: Custom exceptions for the application.
  - **tasks/**: Background tasks and scheduled jobs.
  - **utils/**: Utility functions and helpers.
  - **main.py**: Entry point of the FastAPI application.

## Getting Started

1. **Installation**: Ensure you have Python 3.7+ and install FastAPI and an ASGI server (like uvicorn):
   ```
   pip install fastapi uvicorn
   ```

2. **Running the Application**: Use the following command to run the application:
   ```
   uvicorn app.main:app --reload
   ```

3. **Accessing the API**: Once the server is running, you can access the API documentation at `http://127.0.0.1:8000/docs`.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.