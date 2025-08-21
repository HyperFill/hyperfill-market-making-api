# On-Chain Order-Book Market Maker Settlement System

This project is a NestJS-based server for an on-chain order-book market maker (MM) settlement system. It provides a RESTful API for market makers to submit, amend, and cancel orders, and a WebSocket interface for real-time data feeds. All operations are authenticated using cryptographic signatures.

## Project Overview

The system is designed to allow market makers to interact with an order book through a secure and transparent API. The core features are modeled after platforms like Filament, focusing on signature-based authentication and on-chain settlement.

### Core Features
- **Signature-based Authentication:** Every API request that involves a state change (e.g., placing an order, canceling an order) must be signed with the market maker's private key. The server verifies the signature to ensure the authenticity of the request.
- **RESTful API:** A comprehensive API for managing orders, including placing limit and market orders, canceling orders, and managing collateral.
- **WebSocket Feeds:** Real-time data feeds for the order book and live prices, allowing clients to stay up-to-date with market changes.
- **On-Chain Settlement (Mocked):** The system is designed to settle trades on-chain. In the current implementation, this is mocked by a service that logs the settlement details.

## Project Structure

The project is a standard NestJS application with a modular structure. The main components are located in the `src` directory:

```
src
├── app.module.ts
├── main.ts
├── exchange/
│   ├── dto/
│   ├── settlement/
│   ├── exchange.controller.ts
│   ├── exchange.module.ts
│   └── exchange.service.ts
├── shared/
│   ├── crypto/
│   └── shared.module.ts
└── websocket/
    ├── order-book/
    ├── live-feed/
    └── websocket.module.ts
```

- **`main.ts`**: The entry point of the application.
- **`app.module.ts`**: The root module of the application.
- **`exchange/`**: This module contains all the logic related to the RESTful API for order management.
  - **`dto/`**: Data Transfer Objects (DTOs) used for validating the request bodies of the API endpoints.
  - **`settlement/`**: Contains the mock settlement service.
  - **`exchange.controller.ts`**: The controller that handles the incoming HTTP requests for the `/exchange` route and its sub-routes.
  - **`exchange.service.ts`**: The service that contains the business logic for order management.
- **`shared/`**: This module contains shared utilities that can be used across different modules.
  - **`crypto/`**: Contains the `CryptoService` for handling cryptographic signature verification.
- **`websocket/`**: This module contains the WebSocket gateways for real-time data feeds.
  - **`order-book/`**: The gateway for the order book feed.
  - **`live-feed/`**: The gateway for the live price feed.


## How It Works

1.  **Order Submission:** A market maker creates an order and signs the unique `orderId` with their private key.
2.  **API Request:** The market maker sends a `POST` request to the appropriate API endpoint (e.g., `/exchange`) with the order details, `orderId`, and the `signature`.
3.  **Signature Verification:** The server receives the request and uses the `CryptoService` to verify the signature against the provided `orderId` and the market maker's public address (`account`).
4.  **Order Processing:** If the signature is valid, the `ExchangeService` processes the order. In the current implementation, it sends the order to the mock `SettlementService`.
5.  **WebSocket Broadcast:** The WebSocket gateways periodically broadcast mock data for the order book and live prices to all connected clients.

## Getting Started

### Prerequisites
- Node.js (v16 or higher)
- npm

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository-url>
    ```
2.  Navigate to the `orderbook-mm-server` directory:
    ```bash
    cd orderbook-mm-server
    ```
3.  Install the dependencies:
    ```bash
    npm install
    ```

### Running the Application

To run the application in development mode with watch support:

```bash
npm run start:dev
```

The server will start on `http://localhost:3000`.

## API Endpoints

The following API endpoints are available:

- `POST /exchange`: Place a new order.
- `POST /exchange/cancel`: Cancel an existing order.
- `POST /exchange/update-margin`: Update the margin for a position.
- `POST /exchange/update-tpsl`: Update the take-profit or stop-loss for a position.

*For detailed information about the request and response formats, please refer to the Swagger API documentation (coming soon).*

## WebSocket Feeds

The following WebSocket namespaces are available:

- `/ws/order-book`: Provides real-time updates to the order book.
- `/ws/live-feed`: Provides a real-time feed of market prices.

Clients can connect to these namespaces to receive the data streams.
