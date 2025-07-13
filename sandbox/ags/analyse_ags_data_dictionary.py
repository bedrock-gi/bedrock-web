import marimo

__generated_with = "0.14.10"
app = marimo.App(width="medium")


@app.cell
def _():
    import json

    import marimo as mo
    import polars as pl
    return mo, pl


@app.cell
def _(mo, pl):
    df = pl.read_json(mo.notebook_location() / f"ags4_data_dictionary.json")
    # Using Enums in polars improves efficiency, but makes the marimo column filter not work.
    # df = df.with_columns(
    #     pl.col("group_type").cast(pl.Enum(["In-Situ", "Lab", "Other"]))
    # )
    df
    return (df,)


@app.cell
def _(df, pl):
    # In AGS there are a few tests that comprise of multiple tables.
    # The first three letters of these multi-table groups are the same.
    # The table that describes the test is (mostly) called the General table.
    # The General tables have a G as the last letter of the group name.
    first_3_chars = pl.col("group_name").str.slice(0, 3)
    unique_tests = df.filter(
        # pl.col("group_type").str.contains("Other").not_(),
        pl.col("group_type").cast(pl.Enum(["In-Situ", "Lab", "Other"])) != "Other",
        (
            first_3_chars.is_duplicated()
            & pl.col("group_name").str.contains(first_3_chars + "G").not_()
        ).not_(),
    ).sort(["group_type", "group_name"])
    unique_tests
    return


@app.cell
def _(df, pl):
    multi_table_tests = df.filter(
        pl.col("group_name").str.slice(0, 3).is_duplicated()
    ).sort(["group_type", "group_name"])
    multi_table_tests
    return


if __name__ == "__main__":
    app.run()
