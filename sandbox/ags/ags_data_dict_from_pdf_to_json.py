import marimo

__generated_with = "0.14.10"
app = marimo.App()


@app.cell
def _():
    import json

    import marimo as mo
    import pandas as pd
    import pdfplumber
    return json, mo, pd, pdfplumber


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
    ## Extract Data from .pdf with ChatGPT

    Upload the AGS3-3-1-2005.pdf

    Then use a prompt like this:

    > Put the Groups and Headings table in a CSV with columns group_name,contents,notes,parent_group  
    > The Groups and Headings table starts at the bottom of page 13 and finishes on page 17.

    It might require a bit of chatting with ChatGPT before you get a proper table in your chat. Once you do, you can copy-paste it to a .tsv file. A .tsv file is a Tab Separated Value file instead of CSV - Comma Separated Value file, which is what you get when you copy the table from ChatGPT. TSV's are also handy, because they don't run into issues when one of the values contains a comma...

    Now it could be that ChatGPT doesn't always return the same results and that the table isn't exactly as in the AGS 3 .pdf document. This was the case for me:
    """
    )
    return


@app.cell(hide_code=True)
def _(mo, pd):
    df1 = pd.read_csv(mo.notebook_location() / "ags3_chatgpt_groups_and_headings.tsv", sep="\t")
    df1["df"] = 1
    df2 = pd.read_csv(mo.notebook_location() / "ags3_chatgpt_groups_and_headings2.tsv", sep="\t")
    df2["df"] = 2

    # Concatenate the two DataFrames
    df_concat = pd.concat([df1, df2])

    # Find the duplicate rows
    manual_duplicates = df_concat.duplicated(
        subset=df_concat.columns.difference(["df"]), keep=False
    )

    # Find the rows that are not duplicates (i.e., the rows that are unique to one DataFrame)
    unique_rows = df_concat[~manual_duplicates]

    unique_rows.sort_index()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Extract AGS 3 and 4 Data Dictionaries from their corresponding AGS .pdf documents""")
    return


@app.cell
def _():
    def extract_ags3_data_dict_table(table):
        headings = []
        for row in table[2:]:  # Skip first 2 rows: 1st = title, 2nd = headings
            row = [s.replace("\u2013", "-") for s in row]
            headings.append(
                {
                    "status": None if row[0] == "" else row[0].strip(),
                    "heading": row[1].strip(),
                    "unit": None
                    if row[2] == ""
                    else row[2].strip().replace("\n", " "),
                    "description": row[3].strip().replace("\n", " "),
                    "example": None
                    if row[4] == ""
                    else row[4].strip().replace("\n", " "),
                }
            )
        return headings


    def extract_ags4_data_dict_table(table):
        # Skip rows that don't contain data
        for i, row in enumerate(table):
            if "Suggested\nUnit / Type" in row or "Unit / Type" in row:
                first_data_row = i + 1
                break

        headings = []
        for row in table[first_data_row:]:
            row = [s.replace("\u2013", "-") for s in row if s is not None]
            headings.append(
                {
                    "status": None if row[0] == "" else row[0].strip(),
                    "heading": row[1].strip(),
                    "unit": None
                    if row[2] == ""
                    else row[2].strip().replace("\n", ""),
                    "type": row[3].strip(),
                    "description": row[4].strip().replace("\n", " "),
                    "example": None
                    if row[5] == ""
                    else row[5].strip().replace("\n", " "),
                }
            )
        return headings
    return extract_ags3_data_dict_table, extract_ags4_data_dict_table


@app.cell
def _(mo):
    standards_path = mo.notebook_location().parent.parent / "public" / "standards"
    pdf_dict = {
        3: {
            "pdf_file": standards_path / "AGS3_v3-1-2005.pdf",
            "from_page": 22,
            "to_page": 69,
        },
        4: {
            "pdf_file": standards_path / "AGS4-v4-1-1-2022.pdf",
            "from_page": 18,
            "to_page": 160,
        },
    }
    return (pdf_dict,)


@app.cell
def _(
    extract_ags3_data_dict_table,
    extract_ags4_data_dict_table,
    json,
    mo,
    pdf_dict,
    pdfplumber,
):
    ags_versions = (3, 4)

    for ags_v in ags_versions:
        pdf_file, from_page, to_page = pdf_dict[ags_v].values()

        # List to store extracted data for each group
        extracted_data = []
        previous_group_name = ""
        with pdfplumber.open(pdf_file) as pdf:
            # Adjust the page range based on where the tables are located
            for page_number in range(from_page, to_page):
                page = pdf.pages[
                    page_number - 1
                ]  # pdfplumber is 0-based, so subtract 1
                tables_on_current_page = (
                    page.extract_tables()
                )  # Extract tables from the page

                # Iterate through all tables found on the page
                for table in tables_on_current_page:
                    if ags_v == 3:
                        table_title = table[0][
                            0
                        ].strip()  # Get table title from AGS3
                    elif ags_v == 4:
                        table_title = table[0][
                            1
                        ].strip()  # Get table title from AGS4
                    print(table_title)

                    # Split on the first occurrence of ': '
                    parts = table_title.split(": ", 1)
                    if "Group Name" in parts[0]:
                        # Replace "en dashes" with hyphens
                        group_title = parts[1].replace("\u2013", "-")
                        group_name = group_title.split(" - ")[0]
                        group_description = " - ".join(
                            group_title.split(" - ")[1:]
                        )
                        group_description = group_description.replace("\n", " ")
                        if ags_v == 3:
                            headings = extract_ags3_data_dict_table(table)
                        elif ags_v == 4:
                            headings = extract_ags4_data_dict_table(table)

                        if group_name == previous_group_name:
                            extracted_data[-1]["headings"].extend(headings)
                        else:
                            # Determine group type
                            group_type = "Other"
                            for d in headings:
                                heading = d["heading"]
                                if "SAMP_TOP" in heading:
                                    group_type = "Lab"
                                    break
                                elif group_type == "Other" and (
                                    "HOLE_ID" in heading or "LOCA_ID" in heading
                                ):
                                    group_type = "In-Situ"

                            extracted_data.append(
                                {
                                    "group_name": group_name,
                                    "group_description": group_description,
                                    "group_type": group_type,
                                    "headings": headings,
                                }
                            )

                        previous_group_name = group_name

        # Save the extracted data to a JSON file
        with open(
            mo.notebook_location()
            / f"ags{ags_v}_data_dict_p{from_page}-{to_page}.json",
            "w",
        ) as json_file:
            json_str = json.dump(extracted_data, json_file, indent=2)
    return


@app.cell
def _(json, mo):
    ags_version = 4

    with open(
        mo.notebook_location() / f"ags{ags_version}_manual_groups.json", "r"
    ) as f:
        manual_groups = json.load(f)

    with open(
        mo.notebook_location() / f"ags{ags_version}_data_dictionary.json", "r"
    ) as f:
        extracted_data_dict = json.load(f)
        extracted_groups = [d["group_name"] for d in extracted_data_dict]

    # In case these sets are empty the extraction of all groups went well :)
    print(set(manual_groups) - set(extracted_groups))
    print(set(extracted_groups) - set(manual_groups))
    return


if __name__ == "__main__":
    app.run()
