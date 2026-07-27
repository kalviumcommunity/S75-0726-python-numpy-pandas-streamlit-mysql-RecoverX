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
    """
    Chart for failure distribution by type (TEMPORARY vs PERMANENT).

    Parameters
    ----------
    distribution : list of dict, optional
        Each dict has keys "failure_type" and "count".
        If None or empty, placeholder values are used.

    Returns
    -------
    plotly.graph_objects.Figure
        A donut-style pie chart showing TEMPORARY vs PERMANENT split.
    """
    if distribution:
        temp_count = 0
        perm_count = 0
        for row in distribution:
            ftype = str(row.get("failure_type", "")).upper()
            cnt = int(row.get("count", 0) or 0)
            if ftype == "TEMPORARY":
                temp_count += cnt
            elif ftype == "PERMANENT":
                perm_count += cnt
    else:
        temp_count = 62
        perm_count = 38

    total = temp_count + perm_count
    if total == 0:
        temp_count, perm_count = 1, 1
        total = 2

    pct_temp = round(temp_count / total * 100, 1)
    pct_perm = round(perm_count / total * 100, 1)

    df = pd.DataFrame({
        "Failure Type": [
            f"TEMPORARY  ({pct_temp}%)",
            f"PERMANENT  ({pct_perm}%)",
        ],
        "Count": [temp_count, perm_count],
    })

    colors = ["#f59e0b", "#dc2626"]
    fig = px.pie(
        df,
        values="Count",
        names="Failure Type",
        color_discrete_sequence=colors,
        hole=0.45,
    )
    fig.update_traces(
        textinfo="percent+label",
        textfont_size=13,
        marker=dict(line=dict(color="#ffffff", width=2)),
    )
    fig.update_layout(
        height=350,
        margin={"l": 0, "r": 0, "t": 30, "b": 0},
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
        ),
        annotations=[
            dict(
                text=f"<b>{total}</b><br><span style='font-size:11px;color:#64748b'>Total Failures</span>",
                x=0.5,
                y=0.5,
                font_size=16,
                showarrow=False,
            )
        ],
    )
    return fig


def failure_breakdown_by_response_code_chart(data=None):
    if not data:
        return placeholder_response_code_distribution()

    df = pd.DataFrame(data)
    if df.empty:
        return placeholder_response_code_distribution()

    df["label"] = df.apply(lambda r: f"{r['code']} - {r['description']}", axis=1)
    fig = px.bar(
        df,
        x="label",
        y="count",
        color="code",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(
        height=350,
        margin={"l": 0, "r": 0, "t": 30, "b": 0},
        xaxis_tickangle=-45,
        xaxis_title=None,
        yaxis_title="Failures",
        showlegend=False,
    )
    return fig


def failure_breakdown_by_gateway_chart(data=None):
    if not data:
        gateways = ["Stripe", "Razorpay", "PayU", "PayPal"]
        counts = [40, 30, 20, 10]
        df = pd.DataFrame({"Gateway": gateways, "Count": counts})
    else:
        df = pd.DataFrame(data)
        if df.empty:
            gateways = ["Stripe", "Razorpay", "PayU", "PayPal"]
            counts = [40, 30, 20, 10]
            df = pd.DataFrame({"Gateway": gateways, "Count": counts})
        else:
            df = df.rename(columns={"gateway": "Gateway", "count": "Count"})

    fig = px.pie(
        df,
        values="Count",
        names="Gateway",
        color_discrete_sequence=px.colors.sequential.Reds,
        hole=0.4,
    )
    fig.update_traces(
        textinfo="percent+label",
        textfont_size=12,
        marker=dict(line=dict(color="#ffffff", width=2)),
    )
    fig.update_layout(
        height=350,
        margin={"l": 0, "r": 0, "t": 30, "b": 0},
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.1,
            xanchor="center",
            x=0.5,
        ),
    )
    return fig


def failure_breakdown_by_payment_method_chart(data=None):
    if not data:
        methods = ["Credit Card", "Debit Card", "UPI", "Net Banking"]
        counts = [45, 25, 20, 10]
        df = pd.DataFrame({"Payment Method": methods, "Count": counts})
    else:
        df = pd.DataFrame(data)
        if df.empty:
            methods = ["Credit Card", "Debit Card", "UPI", "Net Banking"]
            counts = [45, 25, 20, 10]
            df = pd.DataFrame({"Payment Method": methods, "Count": counts})
        else:
            df = df.rename(columns={"payment_method": "Payment Method", "count": "Count"})

    fig = px.bar(
        df,
        x="Payment Method",
        y="Count",
        color="Payment Method",
        color_discrete_sequence=["#dc2626", "#ef4444", "#f87171", "#fca5a5"],
    )
    fig.update_layout(
        height=350,
        margin={"l": 0, "r": 0, "t": 30, "b": 0},
        xaxis_title=None,
        yaxis_title="Failures",
        showlegend=False,
    )
    return fig
