Site Map Web Data Extractor

Description:
The Site Map Web Data Extractor is a Python-based tool that efficiently extracts and processes data from webpages linked in an XML sitemap. This utility is designed to gather essential metadata and word frequency data while excluding irrelevant links, such as CDN and social media URLs.

Key Features:

    Link Truncation: Given any starting URL, the tool truncates and gathers all linked URLs found on the page for further analysis.
    Data Extraction: Collects crucial information, including:
        Meta Title: Extracts the meta title of each webpage.
        Meta Description: Extracts the meta description of each webpage.
        Word Frequency Analysis: Counts the occurrences of specified phrases and words across the webpage content.
    Exclusion Filters: Automatically excludes CDN links and social media links from the data collection process to ensure relevant results.
    Data Storage: Organizes and stores extracted data in a sorted manner for easy access and analysis.
    Database Integration: Saves all extracted data into a MySQL database for efficient querying and long-term storage.

Technologies Used:

    Python: The core language for scripting and data processing.
    Requests: For handling HTTP requests and retrieving web content.
    BeautifulSoup: For parsing HTML documents, facilitating the extraction of meta tags and other elements.
    Pandas: To manage and manipulate data efficiently, especially for output formatting.
    SQLAlchemy: To interact with the MySQL database, simplifying data insertion and retrieval.

Getting Started:

    Clone the repository to your local machine.
    Install the required dependencies using pip install -r requirements.txt.
    Configure the settings in the config.py file to specify the target starting URL and any keywords for word frequency analysis.
    Set up your MySQL database and adjust the connection settings in the configuration file.
    Run the extractor script to begin data collection, which will store results directly into your MySQL database in a structured format.

Contributing: Contributions are welcome! Feel free to submit issues or pull requests for enhancements, bug fixes, or additional features.
