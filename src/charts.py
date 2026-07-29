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


def revenue_impact_over_time_chart(data=None):
    if data is None:
        return placeholder_revenue_recovery()

    df = pd.DataFrame(data)

    if df.empty or "period" not in df.columns:
        return placeholder_revenue_recovery()

    df = df.copy()
    df["period"] = pd.to_datetime(df["period"], errors="coerce")
    df = df.dropna(subset=["period"]).sort_values("period")

    if df.empty:
        return placeholder_revenue_recovery()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df["period"],
            y=df.get("recoverable_revenue", 0),
            name="Recoverable",
            fill="tozeroy",
            line_color="#16a34a",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["period"],
            y=df.get("permanently_lost_revenue", 0),
            name="Permanently Lost",
            fill="tonexty",
            line_color="#dc2626",
        )
    )
    fig.update_layout(
        title="Revenue Impact Over Time",
        height=380,
        margin=dict(l=0, r=0, t=50, b=0),
        xaxis_title="",
        yaxis_title="Revenue",
    )
    return fig


def revenue_impact_by_gateway_chart(data=None):
    if data is None:
        return go.Figure()

    df = pd.DataFrame(data)

    if df.empty:
        return go.Figure()

    for col in ["recoverable_revenue", "permanently_lost_revenue"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    fig = px.bar(
        df,
        x="gateway",
        y=["recoverable_revenue", "permanently_lost_revenue"],
        barmode="stack",
        color_discrete_sequence=["#16a34a", "#dc2626"],
        labels={
            "value": "Revenue",
            "gateway": "Gateway",
            "variable": "",
        },
    )
    fig.update_layout(
        title="Revenue Impact by Gateway",
        height=380,
        margin=dict(l=0, r=0, t=50, b=0),
        xaxis_tickangle=-20,
    )
    return fig


def recovery_score_distribution_chart(distribution=None):
    """
    Bar chart for recovery score distribution buckets.
    """
    if not distribution:
        return go.Figure()

    df = pd.DataFrame(distribution)

    fig = go.Figure(
        data=[
            go.Bar(
                x=df["score_range"],
                y=df["count"],
                marker_color="#2563eb",
                text=df["count"],
                textposition="outside",
                hovertemplate=(
                    "Recovery Score: %{x}<br>"
                    "Transactions: %{y}<br>"
                    "<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        title="Recovery Score Distribution",
        height=380,
        margin=dict(l=0, r=0, t=50, b=0),
        xaxis_title="Recovery Score Range",
        yaxis_title="Transactions",
        showlegend=False,
    )

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


def failure_causes_pie_chart(data=None):

    if not data:
        data = [
            {"cause": "Insufficient Funds", "count": 40},
            {"cause": "Do Not Honor", "count": 25},
            {"cause": "Invalid Card", "count": 15},
            {"cause": "Expired Card", "count": 12},
            {"cause": "Network Error", "count": 8},
        ]

    df = pd.DataFrame(data)

    fig = px.pie(
        df,
        names="cause",
        values="count",
        color_discrete_sequence=px.colors.sequential.Reds,
    )

    fig.update_traces(
        textinfo="percent+label",
        marker=dict(line=dict(color="white", width=2))
    )

    fig.update_layout(
        title="Failure Causes (Pie)",
        height=400,
        margin=dict(l=0, r=0, t=50, b=0),
    )

    return fig


def failure_causes_bar_chart(data=None):

    if not data:
        data = [
            {"cause": "Insufficient Funds", "count": 40},
            {"cause": "Do Not Honor", "count": 25},
            {"cause": "Invalid Card", "count": 15},
            {"cause": "Expired Card", "count": 12},
            {"cause": "Network Error", "count": 8},
        ]

    df = pd.DataFrame(data)

    fig = px.bar(
        df,
        x="cause",
        y="count",
        color="cause",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    fig.update_layout(
        title="Failure Causes (Bar)",
        height=400,
        xaxis_title="Failure Cause",
        yaxis_title="Number of Failures",
        xaxis_tickangle=-30,
        showlegend=False,
    )

    fig.update_traces(
        texttemplate="%{y}",
        textposition="outside",
    )

    return fig


def retry_success_rate_per_attempt_chart(data=None):
    """
    Dual-axis chart:
      - Bars: total retry attempts per attempt_number
      - Line: success rate (%) per attempt_number

    Parameters
    ----------
    data : list of dict, optional
        Each dict has keys: attempt_number, total_attempts, successful,
        failed, success_rate. Falls back to placeholder values when empty.
    """
    if not data:
        data = [
            {"attempt_number": 1, "total_attempts": 850, "successful": 510, "failed": 340, "success_rate": 60.0},
            {"attempt_number": 2, "total_attempts": 340, "successful": 204, "failed": 136, "success_rate": 60.0},
            {"attempt_number": 3, "total_attempts": 136, "successful": 68,  "failed": 68,  "success_rate": 50.0},
            {"attempt_number": 4, "total_attempts": 50,  "successful": 20,  "failed": 30,  "success_rate": 40.0},
        ]

    df = pd.DataFrame(data)
    attempt_labels = [f"Attempt {int(n)}" for n in df["attempt_number"]]

    bar_colors = ["#2563eb", "#38bdf8", "#0ea5e9", "#0369a1", "#0c4a6e"]
    color_len = len(bar_colors)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=attempt_labels,
            y=df["total_attempts"],
            name="Total Attempts",
            marker_color=[bar_colors[i % color_len] for i in range(len(df))],
            opacity=0.85,
            hovertemplate=(
                "Attempt %{x}<br>"
                "Total: %{y}<br>"
                "<extra></extra>"
            ),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=attempt_labels,
            y=df["success_rate"],
            name="Success Rate (%)",
            mode="lines+markers+text",
            yaxis="y2",
            line_color="#16a34a",
            line_width=3,
            marker=dict(size=9, color="#16a34a"),
            text=[f"{v}%" for v in df["success_rate"]],
            textposition="top center",
            textfont=dict(color="#16a34a", size=12),
            hovertemplate=(
                "Attempt %{x}<br>"
                "Success Rate: %{y}%<br>"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(title="Retry Attempt Number"),
        yaxis=dict(title="Total Attempts", side="left"),
        yaxis2=dict(
            title="Success Rate (%)",
            overlaying="y",
            side="right",
            range=[0, 105],
            showgrid=False,
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        hovermode="x unified",
    )

    return fig


def retry_success_heatmap_chart(data=None):
    """
    Heatmap chart showing retry success rate by day of week and hour of day.
    """
    if not data:
        data = {
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            "hours": list(range(24)),
            "values": [[0.0 for _ in range(24)] for _ in range(7)],
        }

    days = data.get("days") or ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    hours = data.get("hours") or list(range(24))
    values = data.get("values") or [[0.0 for _ in range(24)] for _ in range(7)]

    matrix = []
    for row in values:
        if len(row) < len(hours):
            row = list(row) + [0.0] * (len(hours) - len(row))
        matrix.append([0.0 if value is None else float(value) for value in row[:len(hours)]])

    if len(matrix) < len(days):
        matrix.extend([[0.0 for _ in range(len(hours))] for _ in range(len(days) - len(matrix))])

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix,
            x=hours,
            y=days,
            colorscale="Viridis",
            zmin=0,
            zmax=100,
            colorbar_title="Success %",
            hovertemplate="Day: %{y}<br>Hour: %{x}<br>Success Rate: %{z}%<extra></extra>",
        )
    )

    fig.update_layout(
        title="Retry Success by Day and Hour",
        height=420,
        margin=dict(l=0, r=0, t=50, b=0),
        xaxis_title="Hour of Day",
        yaxis_title="Day of Week",
    )

    return fig


def retry_timing_analysis_chart(data=None):
    """
    Bar chart for retry timing windows such as 0-6 hrs, 6-12 hrs, and 24-48 hrs.
    """
    if not data:
        data = [
            {"window": "0-6 hrs", "count": 18},
            {"window": "6-12 hrs", "count": 12},
            {"window": "12-24 hrs", "count": 8},
            {"window": "24-48 hrs", "count": 5},
            {"window": "48+ hrs", "count": 2},
        ]

    df = pd.DataFrame(data)
    if df.empty:
        df = pd.DataFrame([{"window": "No data", "count": 0}])

    fig = px.bar(
        df,
        x="window",
        y="count",
        color="window",
        color_discrete_sequence=px.colors.sequential.Blues,
    )

    fig.update_layout(
        height=360,
        title="Retry Timing Windows",
        margin=dict(l=0, r=0, t=50, b=0),
        xaxis_title="Time Window",
        yaxis_title="Observed Retry Intervals",
        showlegend=False,
    )

    return fig

# ---------------------------------------------------------
# Retry Performance by Gateway
# ---------------------------------------------------------

def retry_gateway_performance_chart(data=None):

    if not data:
        data = [
            {
                "gateway": "Stripe",
                "total_retries": 450,
                "successful": 340,
                "success_rate": 75.6,
            },
            {
                "gateway": "Razorpay",
                "total_retries": 310,
                "successful": 205,
                "success_rate": 66.1,
            },
            {
                "gateway": "PayU",
                "total_retries": 260,
                "successful": 165,
                "success_rate": 63.5,
            },
        ]

    df = pd.DataFrame(data)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["gateway"],
            y=df["total_retries"],
            name="Retry Attempts",
            marker_color="#2563eb",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["gateway"],
            y=df["success_rate"],
            name="Success Rate (%)",
            yaxis="y2",
            mode="lines+markers+text",
            text=[f"{x}%" for x in df["success_rate"]],
            textposition="top center",
            line=dict(color="#16a34a", width=3),
        )
    )

    fig.update_layout(
        title="Retry Performance by Gateway",
        height=400,
        xaxis_title="Gateway",
        yaxis_title="Retry Attempts",
        yaxis2=dict(
            title="Success Rate (%)",
            overlaying="y",
            side="right",
            range=[0, 100],
            showgrid=False,
        ),
        hovermode="x unified",
    )

    return fig

# ---------------------------------------------------------
# Retry Performance by Bank
# ---------------------------------------------------------

def retry_bank_performance_chart(data=None):

    if not data:
        data = [
            {
                "bank": "HDFC",
                "total_retries": 500,
                "successful": 390,
                "success_rate": 78.0,
            },
            {
                "bank": "ICICI",
                "total_retries": 420,
                "successful": 305,
                "success_rate": 72.6,
            },
            {
                "bank": "SBI",
                "total_retries": 360,
                "successful": 230,
                "success_rate": 63.9,
            },
        ]

    df = pd.DataFrame(data)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["bank"],
            y=df["total_retries"],
            name="Retry Attempts",
            marker_color="#f59e0b",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=df["bank"],
            y=df["success_rate"],
            name="Success Rate (%)",
            mode="lines+markers+text",
            yaxis="y2",
            text=[f"{x}%" for x in df["success_rate"]],
            textposition="top center",
            line=dict(color="#dc2626", width=3),
        )
    )

    fig.update_layout(
        title="Retry Performance by Bank",
        height=400,
        xaxis_title="Bank",
        yaxis_title="Retry Attempts",
        yaxis2=dict(
            title="Success Rate (%)",
            overlaying="y",
            side="right",
            range=[0, 100],
            showgrid=False,
        ),
        hovermode="x unified",
    )

    return fig
