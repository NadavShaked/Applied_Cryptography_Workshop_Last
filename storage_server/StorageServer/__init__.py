# Standard library imports
from datetime import datetime, timedelta
import atexit

# Third-party library imports
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from flask_cors import CORS

# Local imports
from .api import api_bp, calculate_sigma_mu_and_prove
from .helpers import delete_file_from_storage_server, end_subscription_by_seller, request_funds, get_escrow_data
from .storage import files_details_dict


RUN_JOB_EVERY_IN_SECONDS: int = 20


def create_app():
    # Initialize the Flask app
    app = Flask(__name__)

    # Enable CORS for all routes (or customize as needed)
    CORS(app)

    # Register the API Blueprint for the StorageServer2 app
    app.register_blueprint(api_bp)

    # Initialize the scheduler (used to run jobs in the background)
    scheduler = BackgroundScheduler()

    # Function to check the files and trigger the handle function
    def check_files_to_validate():
        print("Starting to validate files...")

        # Create a copy of the files details dictionary for safe iteration
        files_details_dict_copy = files_details_dict.copy()

        # Iterate over each file's details in the copy of the dictionary
        for filename, file_details in files_details_dict_copy.items():
            validate_every = file_details.get("validate_every")  # Time interval for validation
            last_verify = file_details.get("last_verify")  # Last verification timestamp

            # Debug print to track when validation is due
            print(f"Last verification: {last_verify}, Validate every: {timedelta(seconds=validate_every)}, "
                  f"Next validation: {last_verify + timedelta(seconds=validate_every)}, "
                  f"Current time: {datetime.now()}, Time for validation: {last_verify + timedelta(seconds=validate_every) < datetime.now()}")

            # Check if it's time to validate the file
            if last_verify + timedelta(seconds=validate_every) < datetime.now():
                print(f"Validating file: {filename}")

                # Retrieve escrow details to check subscription status
                escrow_public_key = file_details.get("escrow_public_key")
                escrow_data = get_escrow_data(escrow_public_key)

                is_subscription_ended_by_buyer = escrow_data.get("is_subscription_ended_by_buyer")
                print(f"Subscription ended by buyer: {is_subscription_ended_by_buyer}")

                # If the subscription has ended, request funds
                if is_subscription_ended_by_buyer:
                    print("Subscription ended, requesting funds...")
                    is_get_funds = request_funds(escrow_public_key)

                    # If funds are successfully retrieved
                    if is_get_funds:
                        print(f"Funds received, removing file: {filename}")
                        files_details_dict.pop(filename)    # remove the file from dict
                        delete_file_from_storage_server(filename)   # delete from the storage server
                else:
                    escrow_balance = escrow_data.get("balance")
                    query_size = escrow_data.get("query_size")

                    # Calculate the cost of proving
                    prove_cost = 1.0 + 0.05 * query_size
                    print(f"Escrow balance: {escrow_balance}, Prove cost: {prove_cost}")

                    # If there is enough balance, proceed with proving
                    if escrow_balance >= prove_cost:
                        print(f"Enough balance, proving for file: {filename}")
                        is_proved = calculate_sigma_mu_and_prove(filename, escrow_public_key)

                        # If proving is successful, update the last verification timestamp
                        if is_proved:
                            print(f"File {filename} successfully proved. Updating last verification timestamp.")
                            file_details["last_verify"] = datetime.now()
                    else:
                        print(f"Not enough balance for proving for file: {filename}")

        print("File validation check complete.")

    print(f"Adding job to scheduler to run every {RUN_JOB_EVERY_IN_SECONDS} seconds.")
    scheduler.add_job(check_files_to_validate, 'interval', seconds=RUN_JOB_EVERY_IN_SECONDS, max_instances=1)

    scheduler.start()

    # Graceful shutdown for the scheduler when the app stops
    def shutdown_scheduler():
        # Create a copy of the files details dictionary for safe iteration
        files_details_dict_copy = files_details_dict.copy()

        # Iterate over each file's details in the copy of the dictionary
        for filename, file_details in files_details_dict_copy.items():
            print(f"Processing file: {filename}")

            escrow_public_key = file_details.get("escrow_public_key")
            print(f"Escrow public key for {filename}: {escrow_public_key}")

            # End the subscription by the seller (if applicable)
            print(f"Ending subscription for {filename} using escrow public key {escrow_public_key}...")
            end_subscription_by_seller(escrow_public_key)

        print("Shutting down scheduler...")
        scheduler.shutdown()
        print("Scheduler has been shut down.")

    # Register the shutdown function to be called when the app exits
    atexit.register(shutdown_scheduler)

    return app
