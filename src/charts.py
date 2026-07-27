import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def placeholder_transactions_overview():
    """
    Placeholder chart for transactions overview line chart.
    """
    date_ranges = ["Jun 21", "Jun 28", "Jul 5", "Jul 12", "Jul 19", "Jul 26"]
    success_counts = [1800, 2000, 1950, 2100, 2250, 2300]
    failed_counts = [300, 300, 300, 300, 250, 200]
    df = pd.DataFrame({"Date": date_ranges, "Success": success_counts, "Failed": failed_counts})
    fig = px.line(df, x="Date", y=["Success", "Failed"], markers=True, 
                 color_discrete_sequence=["#16a34a", "#dc2626"])
    fig.update_layout(height=350, margin={"l": 0, "r": 0, "t": 30, "b": 0})
    return fig


def placeholder_failure_distribution():
    """
    Placeholder chart for failure cause distribution pie chart.
    """
    failure_causes = ["Insufficient Funds", "Do Not Honor", "Expired Card", "Invalid CVV", "Network Error"]
    counts = [40, 25, 15, 12, 8]
    df = pd.DataFrame({"Cause": failure_causes, "Count": counts})
    fig = px.pie(df, values="Count", names="Cause", color_discrete_sequence=px.colors.sequential.Reds)
    fig.update_layout(height=350, margin={"l": 0, "r": 0, "t": 30, "b": 0})
    return fig


def placeholder_retry_attempts():
    """
    Placeholder chart for retry attempts distribution bar chart.
    """
    attempts = ["0", "1", "2", "3", "4+"]
    tx_counts = [8500, 2000, 1000, 500, 345]
    df = pd.DataFrame({"Attempts": attempts, "Transactions": tx_counts})
    fig = px.bar(df, x="Attempts", y="Transactions", color="Attempts", 
                 color_discrete_sequence=["#2563eb", "#38bdf8", "#0ea5e9", "#0369a1", "#0c4a6e"])
    fig.update_layout(height=350, margin={"l": 0, "r": 0, "t": 30, "b": 0}, showlegend=False)
    return fig


def placeholder_revenue_recovery():
    """
    Placeholder chart for revenue recovery over time area chart.
    """
    date_ranges = ["Jun 21", "Jun 28", "Jul 5", "Jul 12", "Jul 19", "Jul 26"]
    recovered = [10000, 12000, 14000, 16000, 18000, 20000]
    potential = [15000, 18000, 21000, 24000, 27000, 30000]
    df = pd.DataFrame({"Date": date_ranges, "Recovered": recovered, "Potential": potential})
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Recovered"], name="Recovered", fill="tozeroy", 
                          line_color="#16a34a"))
    fig.add_trace(go.Scatter(x=df["Date"], y=df["Potential"], name="Potential", fill="tonexty", 
                          line_color="#0ea5e9"))
    fig.update_layout(height=350, margin={"l": 0, "r": 0, "t": 30, "b": 0})
    return fig


def placeholder_response_code_distribution():
    """
    Placeholder chart for bank response code distribution.
    """
    codes = ["00", "05", "51", "54", "61", "62"]
    descriptions = ["Approved", "Do Not Honor", "Insufficient Funds", "Expired Card", "Exceeds Withdrawal", "Invalid CVV"]
    counts = [5000, 800, 1200, 300, 400, 300]
    df = pd.DataFrame({"Code": codes, "Description": descriptions, "Count": counts})
    fig = px.bar(df, x="Description", y="Count", color="Code", 
                 color_discrete_sequence=px.colors.qualitative.Set2)
    fig.update_layout(height=350, margin={"l": 0, "r": 0, "t": 30, "b": 0}, xaxis_tickangle=-45)
    return fig


def failure_type_distribution_chart(distribution=None):

    if distribution:
        temp = sum(
            int(row.get("count", 0))
            for row in distribution
            if str(row.get("failure_type")).upper() == "TEMPORARY"
        )

        perm = sum(
            int(row.get("count", 0))
            for row in distribution
            if str(row.get("failure_type")).upper() == "PERMANENT"
        )

    else:
        temp = 60
        perm = 40

    total = temp + perm

    if total == 0:
        temp = 1
        perm = 1
        total = 2

    fig = px.pie(
        names=["Temporary", "Permanent"],
        values=[temp, perm],
        hole=0.45,
        color=["Temporary", "Permanent"],
        color_discrete_map={
            "Temporary": "#f59e0b",
            "Permanent": "#dc2626",
        },
    )

    fig.update_traces(
        textinfo="percent+label",
        marker=dict(line=dict(color="white", width=2))
    )

    fig.update_layout(
        height=380,
        title="Failure Distribution",
        margin=dict(l=0, r=0, t=50, b=0),
    )

    return fig


def failure_breakdown_by_response_code_chart(data=None):

    if not data:
        return placeholder_response_code_distribution()

    df = pd.DataFrame(data)

    if df.empty:
        return placeholder_response_code_distribution()

    df["Response"] = (
        df["code"] + " - " + df["description"]
    )

    fig = px.bar(
        df,
        x="Response",
        y="count",
        color="count",
        color_continuous_scale="Reds",
    )

    fig.update_layout(
        title="Failures by Response Code",
        height=400,
        xaxis_title="",
        yaxis_title="Failures",
    )

    return fig


def failure_breakdown_by_gateway_chart(data=None):

    if not data:
        data = [
            {"gateway": "Stripe", "count": 40},
            {"gateway": "Razorpay", "count": 25},
            {"gateway": "PayU", "count": 15},
            {"gateway": "PayPal", "count": 20},
        ]

    df = pd.DataFrame(data)

    fig = px.pie(
        df,
        names="gateway",
        values="count",
        hole=0.4,
        color_discrete_sequence=px.colors.sequential.Blues,
    )

    fig.update_layout(
        title="Gateway Failure Distribution",
        height=380,
    )

    return fig


def failure_breakdown_by_payment_method_chart(data=None):

    if not data:
        data = [
            {"payment_method": "Credit Card", "count": 45},
            {"payment_method": "Debit Card", "count": 25},
            {"payment_method": "UPI", "count": 20},
            {"payment_method": "Wallet", "count": 10},
        ]

    df = pd.DataFrame(data)

    fig = px.bar(
        df,
        x="payment_method",
        y="count",
        color="payment_method",
    )

    fig.update_layout(
        title="Payment Method Failures",
        height=380,
        xaxis_title="",
        yaxis_title="Failures",
        showlegend=False,
    )

    return fig

