from agents import Runner, SQLiteSession, function_tool, RunContextWrapper
from models import UserAccountContext


@function_tool
def get_user_tier(wrapper: RunContextWrapper[UserAccountContext]):

    return (
        f"The user {wrapper.context.customer_id} has a {wrapper.context.tier} account."
    )


user_account_ctx = UserAccountContext(
    customer_id=1,
    name="nico",
    tier="basic",
)


def main():
    print("Hello from 7-customer-support-agent!")


if __name__ == "__main__":
    main()
