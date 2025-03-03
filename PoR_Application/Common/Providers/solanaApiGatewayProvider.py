import requests


SOLANA_GATEWAY_BASE_URL: str = "http://127.0.0.1:3030"


class SolanaGatewayClientProvider:
    def __init__(self):
        """
        Initialize the ClientProvider with the base URL.
        """
        self.headers = {"Content-Type": "application/json"}

    def _send_request(self, endpoint: str, method: str = "POST", payload=None):
        """
        Helper method to send HTTP requests.

        Args:
            endpoint (str): The API endpoint to hit (relative to base_url).
            method (str): The HTTP method to use (GET, POST, etc.).
            payload (dict): The data to send with the request (for POST/PUT requests).

        Returns:
            response (requests.Response): The response object from the server.
        """
        url: str = f"{SOLANA_GATEWAY_BASE_URL}/{endpoint}"

        if method.upper() == "POST":
            response = requests.post(url, headers=self.headers, json=payload)
        elif method.upper() == "GET":
            response = requests.get(url, headers=self.headers, params=payload)
        else:
            raise ValueError("Unsupported HTTP method")

        return response

    def start_subscription(self,
                           buyer_private_key: str,
                           seller_pubkey: str,
                           u: str,
                           g: str,
                           v: str,
                           query_size: int,
                           number_of_blocks: int,
                           validate_every: int):
        """
        Starts a subscription process for a given buyer and seller in an escrow system.

        Args:
            buyer_private_key (str): The private key of the buyer for signing transactions.
            seller_pubkey (str): The public key of the seller involved in the escrow.
            u (str): The elliptic curve point u, typically in G1, related to the escrow.
            g (str): The elliptic curve point g, related to the public parameters of the system.
            v (str): The elliptic curve point v, generated from the private key of the buyer.
            query_size (int): The size of each query that will be sent in the subscription.
            number_of_blocks (int): The number of blocks to process or query.
            validate_every (int): The frequency with which validation should be performed during the subscription.

        Returns:
            response (requests.Response): The response object from the server indicating success or failure of the subscription request.
        """
        payload = {
            "buyer_private_key": buyer_private_key,
            "seller_pubkey": seller_pubkey,
            "u": u,
            "g": g,
            "v": v,
            "query_size": query_size,
            "number_of_blocks": number_of_blocks,
            "validate_every": validate_every
        }

        return self._send_request("start_subscription", method="POST", payload=payload)

    def add_funds_to_subscription(self, buyer_private_key: str, escrow_pubkey: str, lamports_amount: int):
        """
        Adds funds to an existing subscription by transferring lamports to the escrow account.

        Args:
            buyer_private_key (str): The private key of the buyer initiating the transaction.
            escrow_pubkey (str): The public key of the escrow account to receive the funds.
            lamports_amount (int): The amount of lamports to add to the escrow account.

        Returns:
            response (requests.Response): The response object from the server indicating the success or failure of the fund transfer.
        """
        payload = {
            "buyer_private_key": buyer_private_key,
            "escrow_pubkey": escrow_pubkey,
            "amount": lamports_amount,
        }

        return self._send_request("add_funds_to_subscription", method="POST", payload=payload)

    def end_subscription_by_buyer(self, buyer_private_key, escrow_pubkey):
        """
        Ends the subscription process initiated by the buyer for a given escrow account.

        Args:
            buyer_private_key (str): The private key of the buyer initiating the subscription termination.
            escrow_pubkey (str): The public key of the escrow account associated with the subscription.

        Returns:
            response (requests.Response): The response object from the server indicating the success or failure of the subscription termination request.
        """
        payload = {
            "buyer_private_key": buyer_private_key,
            "escrow_pubkey": escrow_pubkey,
        }

        return self._send_request("end_subscription_by_buyer", method="POST", payload=payload)

    def end_subscription_by_seller(self, seller_private_key, escrow_pubkey):
        """
        Ends the subscription process initiated by the seller for a given escrow account.

        Args:
            seller_private_key (str): The private key of the seller initiating the subscription termination.
            escrow_pubkey (str): The public key of the escrow account associated with the subscription.

        Returns:
            response (requests.Response): The response object from the server indicating the success or failure of the subscription termination request.
        """
        payload = {
            "seller_private_key": seller_private_key,
            "escrow_pubkey": escrow_pubkey,
        }

        return self._send_request("end_subscription_by_seller", method="POST", payload=payload)

    def request_funds(self, user_private_key, escrow_pubkey):
        """
        Requests the release of funds from the escrow account.

        Args:
            user_private_key (str): The private key of the user requesting the funds.
            escrow_pubkey (str): The public key of the escrow account holding the funds.

        Returns:
            response (requests.Response): The response object from the server indicating the success or failure of the fund release request.
        """
        payload = {
            "user_private_key": user_private_key,
            "escrow_pubkey": escrow_pubkey,
        }

        return self._send_request("request_funds", method="POST", payload=payload)

    def generate_queries(self, user_private_key, escrow_pubkey):
        """
        Generates queries for the specified escrow account based on the user's private key.

        Args:
            user_private_key (str): The private key of the user generating the queries.
            escrow_pubkey (str): The public key of the escrow account for which queries are being generated.

        Returns:
            response (requests.Response): The response object from the server indicating the success or failure of the query generation request.
        """
        payload = {
            "user_private_key": user_private_key,
            "escrow_pubkey": escrow_pubkey
        }
        return self._send_request("generate_queries", method="POST", payload=payload)

    def get_queries_by_escrow(self, escrow_pubkey):
        """
        Retrieves queries based on the escrow public key.

        Args:
            escrow_pubkey (str): The escrow public key.

        Returns:
            response (requests.Response): The response object from the server.
        """
        payload = {"escrow_pubkey": escrow_pubkey}
        return self._send_request("get_queries_by_escrow", method="POST", payload=payload)

    def get_escrow_data(self, escrow_pubkey):
        """
        Retrieves data related to an escrow account based on the escrow public key.

        Args:
            escrow_pubkey (str): The public key of the escrow account whose data is being requested.

        Returns:
            response (requests.Response): The response object from the server containing the escrow data or an error message.
        """
        payload = {"escrow_pubkey": escrow_pubkey}
        return self._send_request("get_escrow_data", method="POST", payload=payload)


    def prove(self, seller_private_key, escrow_public_key, sigma, mu):
        """
        Sends a prove request.

        Args:
            seller_private_key (str): The seller's private key.
            escrow_public_key (str): The escrow account public key.
            sigma (str): The base64 encoded 48-byte value.
            mu (str): The mu value as a string.

        Returns:
            response (requests.Response): The response object from the server.
        """
        payload = {
            "seller_private_key": seller_private_key,
            "escrow_pubkey": escrow_public_key,
            "sigma": sigma,
            "mu": mu
        }

        return self._send_request("prove", method="POST", payload=payload)
