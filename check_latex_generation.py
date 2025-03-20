import os
import subprocess

def create_pdf_from_latex(latex_code, output_pdf_path, single_run=False):
    # Ensure the output directory exists
    output_dir = os.path.dirname(output_pdf_path)
    os.makedirs(output_dir, exist_ok=True)

    # Write the LaTeX code to a temporary .tex file in the output directory
    tex_file_name = "temp_latex_file.tex"  # Temporary TeX filename
    tex_file_path = os.path.join(output_dir, tex_file_name)
    with open(tex_file_path, "w") as tex_file:
        tex_file.write(latex_code)

    success_bool = False
    error_messsage = ""
    try:
        # Compile the .tex file into a PDF using latexmk (which handles multiple passes automatically)
        if single_run:
          result = subprocess.run(
              [
                  "pdflatex",             # Generate PDF via pdflatex (could use -xelatex for XeLaTeX, etc.)
                  "-interaction=nonstopmode",    # Do not stop on errors (try to continue compilation)
                  f"-output-directory={output_dir}",  # Directory for output (PDF and aux files)
                  tex_file_path                 # The LaTeX source file to compile
              ],
              check=True,
              capture_output=True,
              text=True
          )
        else:
            result = subprocess.run(
            [
                "latexmk",
                "-pdf",  
                "-f",               # Generate PDF via pdflatex (could use -xelatex for XeLaTeX, etc.)
                "-interaction=nonstopmode",    # Do not stop on errors (try to continue compilation)
                f"-output-directory={output_dir}",  # Directory for output (PDF and aux files)
                tex_file_path                 # The LaTeX source file to compile
            ],
            check=True,
            capture_output=True,
            text=True
        )
        # Print the compilation log from latexmk (stdout and stderr) for debugging
        print("result.stdout: ", result.stdout)
        if result.stderr:
            print("result.stderr : ",result.stderr)

        # Check if the PDF was generated
        generated_pdf = os.path.join(output_dir, tex_file_name.replace(".tex", ".pdf"))
        if os.path.exists(generated_pdf):
            # Rename/move the generated PDF to the desired output path
            os.replace(generated_pdf, output_pdf_path)
            print(f"PDF generated successfully at: {output_pdf_path}")
        else:
            print(f"PDF generation failed. File not found: {generated_pdf}")
        success_bool = True

    except subprocess.CalledProcessError as e:
        # If latexmk exits with an error, print the logs for diagnosis
        print("Error during PDF generation. Please check the LaTeX source and log output.")
        if e.stdout:
            print("e.stdout : ",e.stdout)
            error_messsage += "e.stdout :\n" + e.stdout
        if e.stderr:
            print("e.stderr : ",e.stderr)
            error_messsage += "\ne.stderr :\n" + e.stderr

    finally:
        # Clean up auxiliary files produced during compilation
        aux_extensions = [".aux", ".log", ".out", ".toc", ".fls", ".fdb_latexmk", ".synctex.gz", ".tex"]
        for ext in aux_extensions:
            file_path = os.path.join(output_dir, tex_file_name.replace(".tex", ext))
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as remove_err:
                    # If an auxiliary file cannot be removed, print a warning (but continue)
                    print(f"Warning: Could not remove file {file_path}: {remove_err}")
        
    return success_bool, error_messsage


# import os
# import subprocess

# def create_pdf_from_latex(latex_code, output_pdf_path):
#     # Ensure the output directory exists
#     output_dir = os.path.dirname(output_pdf_path)
#     os.makedirs(output_dir, exist_ok=True)

#     # Step 1: Write the LaTeX code to a .tex file inside the desired output directory
#     tex_file_name = "temp_latex_file.tex"  # Keep the filename consistent
#     tex_file_path = os.path.join(output_dir, tex_file_name)
#     with open(tex_file_path, "w") as tex_file:
#         tex_file.write(latex_code)

#     try:
#         # Step 2: Compile the .tex file into a PDF using pdflatex with -output-directory
#         for _ in range(2):  # Run twice to resolve references
#             result = subprocess.run(
#                 [
#                     "pdflatex",
#                     "-interaction=nonstopmode",
#                     f"-output-directory={output_dir}",
#                     tex_file_path,
#                 ],
#                 check=True,
#                 capture_output=True,
#                 text=True,
#             )
#             print(result.stdout)  # Print compilation log for debugging

#         # Step 3: Verify if the generated PDF exists
#         generated_pdf = os.path.join(output_dir, tex_file_name.replace(".tex", ".pdf"))
#         if os.path.exists(generated_pdf):
#             # Move the generated PDF to the desired output path
#             os.rename(generated_pdf, output_pdf_path)
#             print(f"PDF generated successfully at: {output_pdf_path}")
#         else:
#             print(f"PDF generation failed. File not found: {generated_pdf}")

#     except subprocess.CalledProcessError as e:
#         print("Error during PDF generation. Please check the LaTeX source.")
#         print(e.stdout)
#         print(e.stderr)

#     finally:
#         # Step 4: Clean up auxiliary files generated by LaTeX in the save folder
#         for ext in [".aux", ".log", ".out", ".tex"]:
#             aux_file = os.path.join(output_dir, tex_file_name.replace(".tex", ext))
#             if os.path.exists(aux_file):
#                 os.remove(aux_file)

# def create_pdf_from_latex(latex_code, output_pdf_path):
#     output_dir = os.path.dirname(output_pdf_path)
#     os.makedirs(output_dir, exist_ok=True)

#     tex_file_name = "temp_latex_file.tex"
#     tex_file_path = os.path.join(output_dir, tex_file_name)
    
#     with open(tex_file_path, "w") as tex_file:
#         tex_file.write(latex_code)

#     try:
#         # Compile with xelatex, not pdflatex
#         for _ in range(2):
#             result = subprocess.run(
#                 [
#                     "xelatex",
#                     "-interaction=nonstopmode",
#                     f"-output-directory={output_dir}",
#                     tex_file_path,
#                 ],
#                 check=True,
#                 capture_output=True,
#                 text=True,
#             )
#             print(result.stdout)

#         generated_pdf = os.path.join(output_dir, tex_file_name.replace(".tex", ".pdf"))
#         if os.path.exists(generated_pdf):
#             os.rename(generated_pdf, output_pdf_path)
#             print(f"PDF generated successfully at: {output_pdf_path}")
#         else:
#             print("PDF generation failed. File not found.")

#     except subprocess.CalledProcessError as e:
#         print("Error during PDF generation.")
#         print(e.stdout)
#         print(e.stderr)

#     finally:
#         # Clean up auxiliary files
#         for ext in [".aux", ".log", ".out", ".tex"]:
#             aux_file = os.path.join(output_dir, tex_file_name.replace(".tex", ext))
#             if os.path.exists(aux_file):
#                 os.remove(aux_file)

# Example Usage
latex_code = r"""
\documentclass[12pt]{article}
\usepackage[margin=1in]{geometry}
\usepackage{setspace}
\usepackage{lmodern}
\usepackage[T1]{fontenc}
\usepackage{amsmath, amssymb, graphicx, booktabs, caption, url, hyperref, longtable, array, xcolor, titling, sectsty, titlesec}
\usepackage{float}
\usepackage{pdflscape}
\usepackage{colortbl}
\usepackage{ragged2e}
\usepackage{threeparttablex}
\usepackage{threeparttable}
\usepackage{siunitx}

\allsectionsfont{\sffamily\bfseries}
\setstretch{1.1}
\captionsetup{font={small,it},justification=centering}
\setlength{\droptitle}{-2cm}
\titlespacing{\section}{0pt}{1ex}{0.5ex}

% Define custom column types
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\newcolumntype{C}[1]{>{\centering\arraybackslash}p{#1}}
\newcolumntype{J}[1]{>{\raggedright\arraybackslash}p{#1}}

% Define colors for table rows
\definecolor{tableHeader}{RGB}{220,230,240}
\definecolor{tableRow1}{RGB}{255,255,255}
\definecolor{tableRow2}{RGB}{245,245,245}
\definecolor{myblue}{RGB}{65,105,225}

\hypersetup{colorlinks=true,linkcolor=blue,urlcolor=blue,breaklinks=true}

\title{How ESG Factors are Reshaping Investment Strategies and Governance}
\author{}
\date{}

\begin{document}
\maketitle
\tableofcontents

\section{ESG Integration in Portfolio Selection}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{img_search_save/img_search_1.png}
  \caption{\textit{Integrating ESG factors has become central to many investment strategies, emphasizing both ethical considerations and potential performance benefits.}}
  \label{fig:esg_integration_image}
\end{figure}

\subsection{Overview of ESG Screening Methods}
\textbf{ESG Screening Approaches and Best-in-Class Methods in Investment Portfolios}

\noindent 1. Negative ESG Screening

Negative screening, sometimes referred to as exclusionary screening, involves omitting specific companies or entire sectors from an investment universe if they fail to meet certain environmental, social, or governance (ESG) thresholds.  
a) Common exclusions: Industries that frequently appear on exclusion lists include tobacco, gambling, fossil fuels, or weapons manufacturing.  
b) Rationale: Organizations employing negative screening often aim to align their investments with ethical, religious, or social values. For instance, some faith-based investors exclude companies connected to alcohol or gambling.  
c) Potential trade‐offs: This approach can narrow the portfolio’s exposure. If excluded industries outperform, the portfolio may lag behind broader market benchmarks. However, it can be a clear-cut way to uphold certain moral stances or manage reputational risks.

\noindent 2. Positive ESG Screening

In contrast, positive screening (also called inclusionary screening) focuses on identifying companies with relatively high ESG performance.  
a) Focus on leaders: Portfolio managers seek top-tier ESG performers and rely on specialized rating systems to pinpoint them.  
b) Integration: Positive screening sometimes coexists with exclusionary tactics, granting managers flexibility to weed out problematic industries while still highlighting best ESG performers.  
c) Performance considerations: Firms with robust ESG metrics may show strengthened risk management and better governance structures, which can contribute to stability in returns over the longer term.

\noindent 3. Best-in-Class ESG Methods

Best-in-class methodologies concentrate on selecting top-performing ESG companies within each industry, rather than dismissing entire sectors outright.  
a) Sector-wide comparison: Rather than excluding, for example, the entire energy sector, investors choose those energy companies that have made the greatest strides in ESG dimensions.  
b) Diversification benefit: By not eliminating entire segments of the market, this approach often preserves industry balance and can reduce concentration risk.  
c) Operational examples: Index groups like the Dow Jones Sustainability Indices track leading companies in each sector based on ESG scores, allowing for a systematic screening of top ESG performers.

\textbf{Use in Investment Portfolios}
\begin{itemize}
\item Combining methods: Investors might apply negative screening to remove industries that clash with their values, then overlay a best-in-class strategy on the remaining set for a more nuanced ESG approach.
\item Strategic rationale: Institutions frequently adopt these frameworks to align capital deployment with broader impact goals while still pursuing competitive returns.
\item Performance implications: Studies suggest ESG-oriented portfolios can show resilience over the long run, but actual results depend on factors such as market dynamics, the reliability of ESG data, and how each screening strategy is executed.
\end{itemize}

\subsection{Common ESG Benchmarks and Indices}
\noindent 1. Well-Known ESG Benchmarks and Indices

Environmental, social, and governance (ESG) benchmarks and indices serve as standardized measures for assessing how effectively companies address sustainability issues. Two of the most recognized are the MSCI ESG Indexes and the Dow Jones Sustainability Indices (DJSI). These frameworks guide investors in identifying potentially resilient, responsibly managed, and forward-thinking companies.

\textbf{• MSCI ESG Indexes:}  
-- Construction: MSCI ESG Indexes integrate metrics such as carbon intensity, board composition, labor policies, and overall accountability. They apply both negative screenings (excluding controversial or high-risk sectors) and positive emphasis on firms demonstrating robust governance or environmental practices.  
-- Criteria \& Updates: MSCI refines its methodology annually, reflecting evolving market expectations around climate adaptation, supply-chain responsibilities, and broader social impact.  
-- Use in Practice: Investors often adopt these indexes in portfolios aiming to hedge against future regulatory or reputational risks. Research suggests companies with consistently high ESG scores may be better positioned to navigate long-term market shifts.

\textbf{• Dow Jones Sustainability Indices (DJSI):}  
-- Construction: Managed by S\&P Global, the DJSI selects the top 10\% of leading sustainability performers within indexed universes, drawing on in-depth yearly assessments. These evaluations target environmental management, social programs, and governance structures that mitigate risks while capitalizing on new opportunities.  
-- Relevance: Inclusion in the DJSI is widely touted as a sign of sound ESG practices, pushing companies to enhance transparency and strategically address emerging sustainability challenges. For investors, DJSI alignment often serves as a credible marker of a firm’s resilience and forward-looking strategy.

Beyond these two, a range of other ESG indices exists—such as the FTSE4Good Series, STOXX ESG Indices, and S\&P 500 ESG Index—each employing distinct weighting and scoring frameworks but all emphasizing sustainability benchmarks.

\noindent 2. Relevance to Portfolio Selection

ESG benchmarks and indices offer more than a mere snapshot of corporate sustainability. By incorporating these into portfolio decisions, investors can:
\begin{itemize}
\item Reduce exposure to potential reputational or regulatory risks.
\item Align capital with companies seeking to mitigate social or environmental harms.
\item Take a proactive stance on governance, strengthening accountability and ethical leadership.
\item Capture growth opportunities in areas such as carbon transition and green innovation.
\end{itemize}

\subsection{Data Sources and Quality Considerations}
\noindent Below is a concise overview of major ESG (Environmental, Social, and Governance) data providers, the primary challenges affecting ESG data quality, and common strategies investors employ to bolster reliability.

\noindent 1. Major ESG Data Providers
\begin{itemize}
\item MSCI: MSCI ESG Ratings focus on how well companies manage financially relevant ESG risks and opportunities, covering thousands of firms (notably those in the MSCI All Country World Index). Their rules-based assessments consider industry-specific factors, facilitating comparisons within and across sectors.
\item Sustainalytics: Sustainalytics delivers ESG Risk Ratings for over 16,000 companies, assessing each company’s exposure to key ESG risks and evaluating how effectively those risks are managed. Investors use these ratings across equity, debt, and private markets.
\item Bloomberg: Bloomberg’s ESG scores appraise companies’ management of financially material ESG considerations, with coverage encompassing close to 94\% of global market capitalization. These data integrate directly into the Bloomberg Terminal, allowing for comparative analysis alongside more conventional financial metrics.
\end{itemize}

\noindent 2. Common ESG Data Quality Challenges

\textbf{a) Lack of Standardization:}  
Several frameworks, such as the Global Reporting Initiative (GRI) and the Sustainability Accounting Standards Board (SASB), exist, yet reporting requirements remain voluntary or fragmented. This patchwork hampers the comparability of ESG metrics across different firms, industries, and regions.

\textbf{b) Data Inconsistency:}  
ESG evaluations frequently rely on self-reported figures that may lack external verification. Inconsistent data points—caused by variations in companies’ reporting processes or selective disclosure—undermine the reliability of ESG ratings and comparisons.

\textbf{c) Transparency Concerns:}  
Without established auditing or third-party validations, investors may question the authenticity of published ESG data. “Greenwashing”—where a firm’s sustainability claims outpace its actual practices—can mislead ESG profiles and distort investment decisions.

\noindent 3. How Investors Address Reliability Concerns
\begin{itemize}
\item Combining Multiple Data Sources: Many investors cross-reference ESG information from several providers. This practice mitigates the risk inherent in relying on any single dataset and offers a more well-rounded perspective of a target company’s sustainability track record.
\item Direct Engagement with Companies: Beyond reviewing publicly disclosed data, investors often interact directly with corporate leadership through briefings, questionnaires, and site visits. These dialogues help verify ESG claims, clarify data gaps, and assess the real-world practicality behind corporate sustainability statements.
\item Third-Party Verification: To bolster credibility, some investors commission external verification services. Independent auditors and standardized assurance processes reduce the likelihood of inaccuracies or selective reporting and increase stakeholder confidence in ESG disclosures.
\end{itemize}

\subsection{Potential Impacts on Risk and Return}
Integrating ESG factors into an investment portfolio can meaningfully influence both its risk profile and potential returns. From an empirical standpoint, many studies and meta-analyses suggest that companies with stronger ESG credentials often exhibit favorable financial outcomes, driven in part by reduced operational and reputational risks. At the same time, contradictory or neutral findings do exist—partly because data and methodologies differ across studies. Such variations underscore the need for more rigorous and standardized research, including long-term analyses that look beyond short-term market fluctuations.

Theoretically, ESG integration is posited to mitigate specific kinds of risk—ranging from regulatory sanctions to negative consumer perceptions—ultimately fostering steadier company performance. Nonetheless, there remains debate regarding causality: some argue that only financially secure firms can afford robust ESG initiatives, while others maintain that ESG-focused improvements themselves boost financial well-being. Adding complexity, ESG ratings often vary significantly among providers due to divergent assessment criteria, making direct comparisons challenging and hampering attempts to draw universally applicable conclusions.

Overall, while the body of evidence increasingly points to tangible benefits from ESG integration, practitioners must navigate ongoing gaps in data consistency, standardization, and methodological rigor. Addressing these areas, including the frequency of ESG disclosures and the need for universally accepted rating frameworks, could greatly improve investors’ ability to evaluate the true extent and nature of ESG’s impact on portfolio performance.

\subsection{Comparison of ESG Screening Approaches}
\begin{ThreePartTable}
{\fontsize{6pt}{7pt}\selectfont
\renewcommand{\arraystretch}{1.1}
\begin{longtable}{
    L{2.8cm}
    L{3.5cm}
    L{3.5cm}
    L{3.0cm}
    L{3.2cm}
}
    \caption{\textit{Comparison of Three Main ESG Screening Approaches}} 
    \label{tab:esg_screening_comparison} \\

    \toprule
    \rowcolor{tableHeader}
    \textbf{ESG Screening Method} & \textbf{Rationale} & \textbf{Potential Trade-Offs} & \textbf{Examples} & \textbf{Performance Implications} \\
    \midrule
    \endfirsthead

    \multicolumn{5}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\
    \toprule
    \rowcolor{tableHeader}
    \textbf{ESG Screening Method} & \textbf{Rationale} & \textbf{Potential Trade-Offs} & \textbf{Examples} & \textbf{Performance Implications} \\
    \midrule
    \endhead

    \midrule
    \multicolumn{5}{r}{{\textit{(Continued on next page)}}} \\
    \endfoot

    \bottomrule
    \endlastfoot

    \rowcolor{tableRow1}
    Negative Screening (Exclusionary) 
    & \begin{itemize}
      \item Aligns investments with ethical, religious, or social ideals.
      \item Avoids “sin” stocks or controversial industries.
      \end{itemize}
    & \begin{itemize}
      \item Limits the investable universe if excluded industries outperform.
      \item Can introduce regional or sector biases.
      \end{itemize}
    & \begin{itemize}
      \item Excluding tobacco, gambling, fossil fuels, or weapons manufacturing.
      \end{itemize}
    & \begin{itemize}
      \item Often improves ESG standings without severely harming returns.
      \item Some sector tilts remain possible.
      \end{itemize} \\

    \rowcolor{tableRow2}
    Positive Screening (Inclusionary)
    & \begin{itemize}
      \item Focuses on firms with robust ESG performance.
      \item Aims to capture potential upside from sustainability leaders.
      \end{itemize}
    & \begin{itemize}
      \item Empirical findings vary; some show inflows and brand benefits, others see mixed returns.
      \item Alpha can be inconsistent.
      \end{itemize}
    & \begin{itemize}
      \item Funds or portfolios that include only “ESG leaders.”
      \item Targets top-tier sustainability innovators.
      \end{itemize}
    & \begin{itemize}
      \item Sometimes linked to higher net inflows versus negatively screened funds.
      \item No single universal consensus on performance.
      \end{itemize} \\

    \rowcolor{tableRow1}
    Best-in-Class
    & \begin{itemize}
      \item Retains industry diversification by picking top ESG performers within each sector.
      \item Rewards leaders in every industry.
      \end{itemize}
    & \begin{itemize}
      \item Performance data can be fragmented, varying by provider and sector.
      \item May demand deeper ESG data validation.
      \end{itemize}
    & \begin{itemize}
      \item Selecting top ESG-rated energy or utilities firms while excluding weaker performers.
      \end{itemize}
    & \begin{itemize}
      \item Data is less uniform, but anecdotal evidence suggests it preserves diversification along with ESG benefits.
      \end{itemize} \\

\end{longtable}
}
\end{ThreePartTable}

\textbf{Why This Table Is Relevant:}
\begin{itemize}
\item Highlights how each approach manages moral or ethical considerations, sector exposures, and potential reputational risks.
\item Reflects variety in performance outcomes, illustrating no universal “best” method.
\item Underscores the importance of consistent ESG data and a long-term perspective when evaluating screening strategies.
\end{itemize}

\section{Thematic and Impact Investing Approaches}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{img_search_save/img_search_2.png}
  \caption{\textit{Illustrative concept of thematic and impact investing.}}
  \label{fig:thematic_investing_concept}
\end{figure}

\subsection{Definition of Thematic Investing}
Thematic investing is an approach that focuses on specific trends, ideas, or challenges rather than on conventional sector or geographic classifications. In the context of Environmental, Social, and Governance (ESG) investing, thematic strategies aim to capture the growth potential of areas that address pressing global issues—such as climate change, social inequality, or sustainable resource use—while also seeking to deliver competitive financial returns. By concentrating on transformative forces or technological innovations, thematic investors can align their portfolios with long-term societal and environmental shifts.

Through these examples, thematic ESG investing provides a structured way to align capital with impactful innovations and responsible business models. While this approach can involve higher concentration risk—given the narrower focus—it also enables investors to be proactive contributors to positive global change.

\textbf{Examples and ESG Alignment}
\begin{itemize}
  \item \textit{Clean Energy}: This theme highlights companies driving the transition from fossil fuels to renewable alternatives like solar, wind, and hydrogen power. Investors in this space look beyond immediate market sentiment to focus on long-term adoption curves, policy support, and global commitments to reduce carbon footprints.
  \item \textit{Social Enterprises}: Socially oriented themes may include organizations that tackle issues like affordable housing, rural healthcare, or financial inclusion for underbanked communities. Thematic investors here look for measurable social impact alongside financial performance, often using metrics such as the number of people served or community development milestones.
  \item \textit{Circular Economy and Resource Efficiency}: This theme targets companies and projects that prioritize waste minimization, recycled inputs, or innovative product designs that extend a product’s lifespan. By investing in resource-efficient businesses, thematic investors can support both environmental objectives and the economic gains these practices can generate.
\end{itemize}

\subsection{Measuring and Verifying Impact}
Measuring and verifying impact in ESG-themed or impact investments is crucial to ensure that both financial returns and positive societal or environmental outcomes are being achieved. Below is an overview of the key metrics, frameworks, examples, and current trends shaping impact measurement and verification in this space:

\textbf{Key Metrics and Frameworks}
\begin{itemize}
  \item \textit{Global Reporting Initiative (GRI)}:  
    Provides comprehensive sustainability reporting standards applicable across industries, emphasizing broad stakeholder inclusivity by examining economic, environmental, and social impacts.
  \item \textit{Sustainability Accounting Standards Board (SASB)}:  
    Focuses on industry-specific ESG factors, linking sustainability performance to financial materiality, helping investors compare performance across companies in similar sectors.
  \item \textit{Task Force on Climate-related Financial Disclosures (TCFD)}:  
    Concentrates on climate risks and opportunities, encouraging businesses to integrate climate considerations into core strategies and ensuring consistent climate-related financial reporting.
  \item \textit{Corporate Sustainability Reporting Directive (CSRD)}:  
    Directs European companies and those in their supply chains to harmonize sustainability reporting, expanding requirements for transparency and accountability across various ESG dimensions.
\end{itemize}

\textbf{Examples of Practical Application}
\begin{itemize}
  \item \textit{Tesla}: Issues an annual Impact Report highlighting emissions reductions, renewable energy adoption, and responsible sourcing, using engaging data visuals to document progress year-over-year.
  \item \textit{Toyota}: Publishes a Sustainability Report focusing on low- or zero-emission technologies, such as hybrids and hydrogen fuel cells, demonstrating large-scale circular economy practices within the automotive sector.
\end{itemize}

\textbf{Current Trends and Developments (as of 2025)}
\begin{itemize}
  \item \textit{Technological Advancements}: AI-driven analytics platforms and blockchain solutions are streamlining data gathering, enabling more precise and auditable impact measurement.  
  \item \textit{Regulatory Momentum}: Governments worldwide are moving toward standardized ESG disclosures, compelling organizations to adopt formal frameworks.  
  \item \textit{Broader Priorities}: Stakeholders are paying closer attention to climate resilience, product innovation, and equality initiatives, demanding clear, measurable results.
\end{itemize}

\subsection{Current Market Trends and Challenges}
\textbf{Strong Demand and Focus on Impact}  
As of early 2025, thematic and impact investing maintain strong momentum, driven by growing awareness of sustainability issues and societal needs. Real estate and infrastructure projects stand out for addressing long-term concerns like urban development, housing shortages, and climate-change resilience. There is also an increased emphasis on tangible outcomes, with investors scrutinizing metrics to ensure commitments translate into genuine benefits.

\textbf{Performance Drivers and Risks}  
\begin{itemize}
  \item \textit{AI and Technological Innovation}: Advances in AI are reshaping supply chains and energy usage, potentially boosting returns for investments in smart infrastructure, clean energy, and efficient housing.  
  \item \textit{Climate-Related Volatility}: Heightened weather disruptions bring greater risk, especially in agriculture and real estate, making climate resilience a key factor for both investors and companies.
\end{itemize}

\textbf{Liquidity Considerations}  
\begin{itemize}
  \item \textit{Evolving Interest Rate Environment}: With the end of an ultra-low interest rate era, private equity and credit markets are shifting. Investors still seek mission-driven projects but must balance tighter financing conditions.  
  \item \textit{Market Depth}: Liquidity remains limited in certain niche ventures. Some funds adopt longer investment horizons or explore creative financing structures to address this.
\end{itemize}

\textbf{Regulatory Pressures and ESG Integration}  
The regulatory landscape varies significantly by region. Europe is advancing rigorous sustainability mandates, while the United States experiences shifting attitudes toward ESG disclosure. Corporate governance also plays a growing role, with leaders prioritizing climate risk, water management, and equitable labor practices as strategic concerns.

\textbf{Persistent Data and Measurement Challenges}  
Major issues include the lack of universally accepted impact measurement standards, reliance on multiple frameworks, and occasional skepticism around “greenwashing.” Increasingly, investors rely on independent verification and rigorous data sources to validate impact results.

\subsection{Role of Specialized Funds}
\textbf{Specialized Funds (ETFs and Mutual Funds) in Thematic and Impact Investing}  
Specialized funds, particularly Exchange-Traded Funds (ETFs) and mutual funds, have become central to deploying capital toward social or environmental objectives. By focusing on clean energy, social enterprises, and circular economy practices, these funds offer a streamlined, pooled investment approach. ETFs often provide intraday tradability and lower fees, although their narrow investment focus can entail concentrated risks. Mutual funds, meanwhile, trade at net asset value and sometimes incorporate an active management style aligned with ESG indicators, which may lead to higher fees and performance variance.

\textbf{Meeting Investor Demand and Market Outlook}
\begin{itemize}
  \item \textit{Value Alignment}: Many investors seek a “double bottom line,” combining traditional returns with social or environmental benefits. Specialized ETFs and mutual funds enable straightforward alignment with these objectives.  
  \item \textit{Product Innovation}: Asset managers have introduced new funds addressing targeted themes like smart cities or innovative healthcare technologies, especially in the ETF sphere due to tradability and lower operating costs.  
  \item \textit{Performance Considerations}: Returns depend on regulatory, technological, and macroeconomic factors. Managers combine fundamental analysis with ESG data to balance potential gains and risks.  
  \item \textit{Future Developments}: As demand for purpose-driven investments grows, these funds will offer more advanced ESG analytics, clearer regulatory guidance, and deeper engagement from fund managers seeking to assure robust theme alignment.
\end{itemize}
\section{Measuring ESG-linked Returns}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{img_search_save/img_search_3.png}
  \caption{\textit{Illustrative concept of key ESG factors influencing corporate performance.}}
  \label{fig:primary_esg_image}
\end{figure}

\subsection{Key Performance Metrics for ESG}
Common ESG performance metrics typically span three primary categories—Environmental, Social, and Governance—to capture the breadth of potential impacts on companies’ operations and returns.
\begin{itemize}
\item \textbf{Environmental metrics} often address greenhouse gas (GHG) emissions (commonly covering Scope 1, 2, and in some cases Scope 3), energy usage and efficiency, and methods of waste and resource management. These indicators help assess how companies are mitigating pollution risks and optimizing resource consumption.

\item \textbf{Social metrics} highlight workforce diversity and inclusion, human capital management (e.g., retention, development, workplace safety), and community engagement, reflecting how organizations maintain positive stakeholder relationships. In sectors relying heavily on consumer trust, such as technology or finance, data protection and customer welfare are also major concerns.

\item \textbf{Governance metrics} focus on board composition and independence, alignment of executive compensation with ESG targets, shareholder rights, and ethical conduct. Strong governance frameworks can help ensure transparent decision-making processes and long-term stewardship of company resources.
\end{itemize}

Sector-specific nuances typically emerge based on materiality. For instance, energy-intensive industries may emphasize emissions trajectories and renewable energy sourcing, whereas data-driven companies may weigh cybersecurity and data stewardship more heavily. Regardless of sector, investors increasingly expect clarity on how these metrics link to financial outcomes, including executive incentives and overall risk exposure. Organizations such as MSCI and Sustainalytics provide standardized evaluation frameworks to facilitate comparability, and regulatory bodies (e.g., the OECD) underscore the need for consistent, reliable data to strengthen accountability and investor confidence.

\subsection{Quantitative vs. Qualitative Evaluation Methods}
Investors combine quantitative and qualitative methods to evaluate ESG-linked returns, leveraging data-driven insights while also accounting for nuanced organizational dynamics.

\textbf{Quantitative Methods}
\begin{itemize}
\item \textit{Statistical Modeling and Hypothesis Testing}: Analysts validate hypotheses regarding ESG factors and cost of capital using large datasets. Evidence indicates that companies with robust ESG practices may benefit from better risk-adjusted returns, while weaker ESG coherence can lead to higher capital costs or elevated volatility.
\item \textit{AI and Big Data Analysis}: Advanced analytics techniques (e.g., natural language processing) parse disclosures and unstructured data for patterns, uncovering risks in supply chains or governance structures.
\item \textit{Portfolio Optimization Tools}: ESG-related metrics, such as emissions or board diversity, can be integrated into optimization models alongside traditional measures to align a portfolio with sustainability and risk objectives.
\end{itemize}

\textbf{Qualitative Methods}
\begin{itemize}
\item \textit{Narrative and Stakeholder Assessments}: Evaluations grounded in the UN Sustainable Development Goals (SDGs) or management interviews help gauge the depth of a company’s ESG commitment.
\item \textit{Engagement and Dialogue}: Direct shareholder or community engagement highlights intangible risks (e.g., worker safety culture) and innovative sustainability efforts not yet recognized by the market.
\item \textit{Holistic Evaluation}: Layering soft signals (e.g., site visits, interviews) with quantitative data provides a broader perspective of a firm’s ESG integration and risk profile.
\end{itemize}

\subsection{Debates Over Performance vs. Traditional Benchmarks}
ESG-driven portfolios, which integrate environmental, social, and governance considerations, spark ongoing debate on whether they underperform or outperform traditional benchmarks.

\textbf{Divergent Empirical Findings}
\begin{itemize}
\item Many meta-analyses suggest a positive or neutral link between ESG practices and financial outcomes, due to factors like enhanced brand reputation and risk management.
\item Other research indicates periods of underperformance when sectors excluded by ESG screens experience market upswings, limiting full diversification.
\end{itemize}

\textbf{Influence of Sector Inclusion and Exclusion}
\begin{itemize}
\item Critics note that omitting certain sectors may forgo returns, especially during cyclical upturns.
\item Proponents emphasize that capital reallocation away from weaker ESG profiles can reduce risks from regulatory penalties or environmental incidents.
\end{itemize}

\textbf{Regulatory and Benchmark Evolution}
\begin{itemize}
\item Specialized ESG indices and climate-focused benchmarks enhance comparability while still evolving toward standardized data and reporting criteria.
\item Enhancements to regulatory mandates may improve ESG data consistency, though disjointed scoring methodologies can hamper direct portfolio comparisons.
\end{itemize}

\textbf{Data and Measurement Challenges}
\begin{itemize}
\item Varying rating agencies and inconsistent scoring systems make direct benchmarking difficult.
\item “Greenwashing” concerns persist, where portfolios claim ESG strengths that fail to align with real-world practices.
\end{itemize}

\subsection{Real-world Case Studies and Data Points on ESG-driven Returns}
Several real-world examples demonstrate that companies strong in ESG often outperform their peers, attributed to more efficient operations, reduced risk, and alignment with rising regulatory and societal expectations.

\textbf{Evidence and Practical Examples}
\begin{itemize}
\item Analyses by Kroll and MSCI highlight patterns of stronger earnings fundamentals and lower downside risk in firms that actively engage in ESG initiatives.
\item ESG-focused ETFs, such as the BNY Mellon Women’s Opportunities ETF (BKWO) or the Franklin Responsibly Sourced Gold ETF (FGDL), have shown returns surpassing 40\% in early 2025. Nonetheless, the commercial viability of ESG funds depends on sufficient scale and ongoing investor support.
\end{itemize}

\textbf{Insights from Academic Research}
\begin{itemize}
\item Studies in the \textit{Journal of Ecohumanism} and by Cameron Academy underscore that effective governance structures, transparent sustainability reporting, and thoughtful divestment strategies can yield positive or neutral financial impacts.
\item Research in Turkey published in \textit{JEMI} reveals a generally positive influence of environmental and governance practices on return on equity (ROE), with more nuanced effects on valuation metrics in certain local markets.
\end{itemize}

\subsection{Illustrative Table of ESG Categories}
\begin{ThreePartTable}
{\fontsize{6pt}{7pt}\selectfont
\renewcommand{\arraystretch}{1.1}
\begin{longtable}{
    L{2.5cm}
    L{5cm}
    L{5cm}
}
    \caption{\textit{ESG Categories, Metrics, and Sector-Specific Nuances}} \label{tab:esg_categories} \\
    \toprule
    \rowcolor{tableHeader}
    \textbf{Category} & \textbf{Key Metrics} & \textbf{Example Sector-Specific Nuances} \\
    \midrule
    \endfirsthead

    \multicolumn{3}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\
    \toprule
    \rowcolor{tableHeader}
    \textbf{Category} & \textbf{Key Metrics} & \textbf{Example Sector-Specific Nuances} \\
    \midrule
    \endhead

    \midrule
    \multicolumn{3}{r}{{\textit{(Continued on next page)}}} \\
    \endfoot

    \bottomrule
    \endlastfoot

    \rowcolor{tableRow1}
    Environmental 
    & \begin{itemize}
      \item GHG Emissions (Scope 1, 2, 3)
      \item Energy Usage \& Efficiency
      \item Waste \& Resource Management
      \end{itemize} 
    & Energy-Intensive Sectors \newline Emissions Trajectories, Renewable Energy Sourcing \\

    \rowcolor{tableRow2}
    Social 
    & \begin{itemize}
      \item Workforce Diversity \& Inclusion
      \item Human Capital Management
      \item Community Engagement
      \item Data Protection \& Customer Welfare
      \end{itemize}
    & Data-Driven Sectors \newline Cybersecurity, Data Stewardship \\

    \rowcolor{tableRow1}
    Governance 
    & \begin{itemize}
      \item Board Composition \& Independence
      \item Executive Compensation Alignment
      \item Shareholder Rights
      \item Ethical Conduct
      \end{itemize}
    & \textit{No additional specification} \\
\end{longtable}
}
\end{ThreePartTable}
\section{ESG Product Innovation}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{img_search_save/img_search_4.png}
  \caption{\textit{Depiction of ESG-oriented investment strategies.}}
  \label{fig:esg_product_innovation_primary}
\end{figure}

\subsection{Overview of ESG Financial Products}

Below is a concise overview of several prominent ESG financial products, highlighting newer trends and real-world factors that shape these instruments.

\textbf{Existing ESG Financial Products}

\noindent 1. ESG Bonds  
\textbf{a. Definition and Purpose:}  
ESG bonds are fixed-income securities whose proceeds primarily support initiatives with positive environmental, social, or governance outcomes. They can be issued by corporations, municipalities, or governments.

\noindent \textbf{b. Structure:}
\begin{itemize}
  \item Green Bonds: Focus on environmental projects, such as renewable energy or pollution prevention.
  \item Social Bonds: Fund social programs like affordable housing or healthcare access.
  \item Sustainability Bonds: Combine environmental and social objectives.
  \item Sustainability-Linked Bonds: Tie the bond’s financial terms (e.g., the coupon rate) to specific sustainability performance targets (SPTs), rewarding or penalizing issuers based on their progress.
\end{itemize}

\textbf{c. Market Size and Adoption:}  
As of mid-2024, global ESG debt exceeded US\$6.5 trillion, reflecting strong demand for transparent, impact-driven financing solutions.

\noindent 2. Sustainability-Linked Loans (SLLs)  
\textbf{a. Defining Attributes:}  
Unlike traditional ESG loans, sustainability-linked loans adjust interest rates or other terms according to the borrower’s performance on predefined ESG metrics (SPTs).

\noindent \textbf{b. Incentive Structure:}  
Borrowers who meet or surpass their sustainability targets typically receive reduced borrowing costs, while missing these targets can result in higher costs.

\noindent \textbf{c. Guiding Principles:}  
The Sustainability Linked Loan Principles (SLLP) encourage robust goal setting, clear reporting, and external reviews to ensure credibility and accountability.

\noindent 3. ESG ETFs  
\textbf{a. Core Concept:}  
ESG-themed exchange-traded funds (ETFs) track baskets of securities that meet specified environmental, social, or governance standards. Many emphasize excluding industries such as fossil fuels, manufacturing firearms, or operating casinos.

\textbf{b. Growth and Performance:}  
ESG ETFs benefit from the liquidity and diversification qualities of traditional ETFs. By late 2024, inflows to ESG-focused ETFs and open-end funds reached record levels of US\$16 billion in a single quarter, though annual totals were somewhat lower than in prior peak periods.

\textbf{c. Appeal to Investors:}  
Beyond aligning portfolios with ethical considerations, ESG ETFs aim to reduce long-term exposure to environmental and social risks. They often appeal to investors seeking both market returns and measurable social or environmental impact.

\subsection{Market Demand and Investor Profiles}

\noindent 1. Current Market Demand for ESG-Linked Products  

The market for ESG-linked products has been expanding at a rapid pace. Projections indicate that by 2030, the sustainable finance market could exceed US\$2.5 trillion, rising from approximately US\$750 billion in 2024 and growing at a compound annual growth rate (CAGR) of around 23\%. Several factors converge to drive this growth:

\textbf{a. Impact Investing and Sustainability Focus:}  
An increasing share of investors continue to prioritize social and environmental considerations, placing impact investing at the forefront of portfolio decisions. This aligns with broader global efforts, including the Paris Agreement and the UN SDGs, which encourage channeling capital toward sustainable development.

\textbf{b. Strong Performance of Selected ESG Assets:}  
The equities segment dominates the sustainable finance market, as companies with robust ESG strategies often demonstrate resilience and long-term value creation. Likewise, ESG-focused ETFs and index funds have seen substantial inflows due to a combination of retail and institutional interest.

\textbf{c. Heightened Regulatory and Public Attention:}  
Regions like Europe have taken a lead in promoting stringent ESG regulations and accompanying best practices, lending support to a strong ecosystem that drives transparency. At the same time, global commitments to reduce environmental harm and improve social outcomes have stimulated additional demand for ESG-themed instruments such as green bonds and sustainability-linked loans.

\noindent 2. Typical Investor Profiles or Motivations  

ESG-linked products draw both institutional and retail investors, though institutions—including pension funds, insurance companies, and asset managers—remain primary buyers given their larger asset bases. Several themes emerge:

\textbf{a. Institutional Integration:}  
Many institutional investors have formally integrated ESG considerations into their mandates to mitigate risk and enhance returns. They rely heavily on both proprietary analytic models and third-party ESG ratings, underscoring the importance of consistent and high-quality ESG data.

\textbf{b. Retail Awareness and Preferences:}  
Retail investors increasingly show a preference for accountability and transparency. Mutual funds and ETFs offering ESG exposure have proliferated, reflecting this growing retail demand. Successfully addressing retail expectations of clarity and measurable impact is key to sustaining long-term interest.

\textbf{c. Avoidance of “Greenwashing” Risks:}  
Across both institutional and retail segments, concerns over greenwashing loom large. Investors expect credible standards and disclosures, focusing on whether companies are legitimately improving their environmental and social impact rather than merely rebranding existing activities under an ESG label.

\textbf{d. Geographic Nuances:}  
European and Canadian investors often report a comparatively stronger tilt toward ESG-labeled products, partially driven by region-specific policies and cultural norms. In contrast, some segments of the US market remain more yield-focused, though overall interest in ESG-led instruments continues to trend upward.

\begin{ThreePartTable}
{\fontsize{6pt}{7pt}\selectfont
\renewcommand{\arraystretch}{1.1}
\begin{longtable}{
    L{2.6cm}
    L{3.8cm}
    L{4.5cm}
    L{3.0cm}
}
    \caption{\textit{Typical Investor Profiles and Motivations}} 
    \label{tab:investor_profiles} \\
    \toprule
    \textbf{Investor Type} & \textbf{Integration of ESG} & \textbf{Motivations} & \textbf{Geographic Nuances} \\
    \endfirsthead

    \multicolumn{4}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\
    \toprule
    \textbf{Investor Type} & \textbf{Integration of ESG} & \textbf{Motivations} & \textbf{Geographic Nuances} \\
    \endhead

    \endfoot

    \bottomrule
    \endlastfoot

    Institutional &
    Formally integrate ESG considerations to mitigate risk and enhance returns. Rely on both proprietary analytic models and third-party ESG ratings. &
    Larger-scale investments targeting stability and long-term value creation. &
    European and Canadian investors often exhibit a stronger tilt toward ESG-labeled products. \\

    Retail &
    Prefer accountability and transparency in ESG offerings. &
    Expect clear and measurable impact from ESG investments. &
    Some US market segments remain more yield-focused, though ESG interest is trending upward. \\

\end{longtable}
}
\end{ThreePartTable}

\subsection{Regulatory Considerations for New Products}

Regulations governing the creation, labeling, and distribution of ESG-focused products have grown more rigorous, primarily to improve transparency and combat greenwashing. In the European Union, the Corporate Sustainability Reporting Directive (CSRD) requires companies (including certain non-EU entities operating in the EU) to disclose a wide array of ESG metrics, such as carbon footprint, workforce diversity, and governance structures. The Sustainable Finance Disclosure Regulation (SFDR) compels asset managers and other financial market participants to integrate ESG considerations into their investment processes, detailing methodology and intended sustainability outcomes in product documentation. Meanwhile, the EU Taxonomy acts as a classification tool to help market participants identify whether an economic activity meets specified sustainability criteria.

In the United States, the Securities and Exchange Commission (SEC) has finalized guidelines stating that listed firms must reveal climate-related data (e.g., greenhouse gas emissions, risk assessments) in annual filings. These rules aim to enable investors to compare companies on a reliable basis, although the initial focus is primarily environmental disclosures. At the international level, United Nations–backed protocols (like the UN Global Compact) and forthcoming guidelines from the International Organization for Standardization (ISO) continue to shape broad principles around responsible business conduct, though binding product-level rules in these domains are still maturing.

As investors increasingly demand verifiable ESG claims, product labeling standards are emerging to authenticate green or sustainable credentials. The SFDR references “Article 8” or “Article 9” designations, for instance, signaling different levels of ESG integration or impact. However, a unified global labeling framework remains absent, creating variations in product classification across regions. Distributors of ESG-focused offerings must therefore remain attuned to evolving rules on disclosure and marketing, ensuring that any “green,” “social,” or “sustainability” labels accurately reflect the underlying investments. Failure to align product documentation—and by extension distribution activities—with recognized regulations can expose issuers and asset managers to reputational risks and potential regulatory action.

\subsection{Potential Future Product Directions}

\noindent 1. Technology Integration  

\textbf{a. Artificial Intelligence (AI)}  
AI is poised to become increasingly integral to ESG financial products. Its ability to aggregate and standardize vast amounts of data from inconsistent sources can help investors pinpoint early risks and opportunities. Predictive analytics can flag irregularities or trends more rapidly than manual methods, ultimately leading to a more reliable, transparent assessment of sustainability performance.

\textbf{b. Blockchain}  
Blockchain-based reporting mechanisms are gaining momentum as a means to guarantee accuracy and traceability in ESG data. Utilizing an immutable ledger bolsters investor confidence in disclosures and mitigates the risk of data manipulation. In sustainability-linked products, for example, blockchain can track fund allocations and link them to measurable social or environmental outcomes.

\textbf{c. Big Data Analytics}  
With ESG metrics spanning environmental, social, and governance dimensions, big data analytics can efficiently process unstructured information (like news feeds or supply chain logs) to reveal hidden risks or correlations. By leveraging advanced analytical models, financial institutions can more effectively craft portfolios that align with emerging ESG goals, such as reaching net-zero emissions or supporting social equity initiatives.

\noindent 2. New ESG Themes  

\textbf{a. Biodiversity and Ecosystem Preservation}  
As the conversation around ESG matures, biodiversity has become a top priority for many stakeholders. Investors increasingly expect companies to disclose their ecosystem impacts, leading to funds and bonds that bolster conservation efforts. These developments underscore a shift toward broader ecological accountability, beyond just carbon mitigation.

\textbf{b. Social Justice and Community Development}  
Beyond environmental measures, social justice themes have been gaining traction, appearing in newer sustainability-linked instruments. Diversifying workplaces, reinforcing equitable pay, and improving local community resources are becoming quantifiable targets in ESG offerings. This trend not only responds to public demand for fairer outcomes but also meets expanding regulatory expectations for measurable social impact.

\subsection*{Visual Illustrations of ESG Market Growth}

Below are two plots that illustrate the scale and projected growth of ESG financial products:

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{save_viz/plot/plot_4_1.png}
  \caption{\textit{Bar Chart Comparing ESG-Related Monetary Figures for 2024 and 2030.}}
  \label{fig:bar_chart_esg}
\end{figure}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{save_viz/plot/plot_4_2.png}
  \caption{\textit{Line Chart Depicting Sustainable Finance Market Growth from 2024 to 2030 (23\% CAGR).}}
  \label{fig:line_chart_esg}
\end{figure}

\noindent \textbf{Key numeric data points related to these figures include:}
\begin{itemize}
  \item Global ESG Debt Market Size (mid-2024): \$6.5 trillion
  \item Inflows to ESG-Focused ETFs (late 2024, single quarter): \$16 billion
  \item Sustainable Finance Market Size (2024): \$750 billion
  \item Projected Sustainable Finance Market Size (2030): \$2,500 billion
  \item Compound Annual Growth Rate (2024--2030): 23\%
\end{itemize}
\section{Challenges in ESG Investment \& Asset Management}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{img_search_save/img_search_5.png}
  \label{fig:primary_esg_image}
\end{figure}

\subsection{Data Reliability and Comparability Issues}
Data Reliability and Comparability Challenges in ESG Integration

\noindent 1. Data Reliability Issues

ESG data reliability hinges on the accuracy, consistency, and completeness of information captured from corporations, third-party providers, and voluntary disclosures. One of the primary challenges is the inconsistent quality of self-reported metrics, which can be selectively disclosed or presented in ways that favor a company’s image. This issue is exacerbated by the absence of uniform verification protocols, resulting in varying degrees of transparency and potential data gaps. In addition, many ESG ratings rely on data-gathering formulas that differ by provider. For instance, some rating organizations might weigh environmental factors more heavily than social or governance components, while others may incorporate broader qualitative assessments. Such variations can lead to contradictory evaluations of the same firm’s ESG performance, hindering reliability.

Regulatory fragmentation further complicates reliability. Different jurisdictions impose distinct criteria for ESG reporting, creating a patchwork of frameworks. Companies with multinational operations often must reconcile disparate reporting requirements, producing nuanced or even conflicting ESG data across regions. Recent developments—such as sustainability-related disclosure mandates and evolving standards—are helping address some of these inconsistencies but have not yet delivered a definitive global template.

\noindent 2. Data Comparability Challenges

Comparability challenges emerge when investors and stakeholders attempt to aggregate or benchmark ESG data across different entities, industries, or geographies. The lack of a universally accepted reporting standard—despite the growing prominence of frameworks like the Global Reporting Initiative (GRI), Sustainability Accounting Standards Board (SASB), and the Task Force on Climate-related Financial Disclosures (TCFD)—continues to hamper clear comparisons. When rating agencies each use proprietary methodologies, two companies with identical performance may end up with highly dissimilar ESG scores.

Moreover, ongoing disagreement among ESG ratings providers underscores the complexity: some studies indicate rating correlations can vary widely, even showing negative relationships for certain measures. This inconsistency prevents investors from confidently drawing parallels between businesses or funds, complicates the benchmarking process, and adds uncertainty to capital allocation decisions. To mitigate these problems, some investors are experimenting with rating aggregation methods that synthesize various data sources into a single, more robust measure of ESG performance. Others engage directly with companies to validate reported metrics and gain deeper insights into ESG practices. While increasing attention on standardized disclosure frameworks may help consolidate different approaches, true comparability likely depends on broader convergence of regulations and methodologies across global markets.

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{save_viz/plot/plot_5_1.png}
  \caption{\textit{Illustrative correlation coefficients among different ESG rating providers.}}
  \label{fig:esg_correlations}
\end{figure}

\begin{ThreePartTable}
{\fontsize{6pt}{7pt}\selectfont
\renewcommand{\arraystretch}{1.1}
\begin{longtable}{
    L{2.5cm} L{5.0cm} L{4.0cm} L{4.0cm} L{3.0cm}
}
    \caption{\textit{Key Challenges in ESG Data Reliability and Comparability}} \label{tab:esg_reliability_challenges} \\
    \toprule
    \rowcolor{tableHeader}
    \textbf{Challenge Type} & \textbf{Description} & \textbf{Real-World Example} & \textbf{Impact} & \textbf{Reference} \\
    \midrule
    \endfirsthead

    \multicolumn{5}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\
    \toprule
    \rowcolor{tableHeader}
    \textbf{Challenge Type} & \textbf{Description} & \textbf{Real-World Example} & \textbf{Impact} & \textbf{Reference} \\
    \midrule
    \endhead

    \midrule
    \multicolumn{5}{r}{{\textit{(Continued on next page)}}} \\
    \endfoot

    \bottomrule
    \endlastfoot

    \rowcolor{tableRow1}
    Inconsistent quality of self-reported metrics &
    Companies sometimes selectively disclose or misreport ESG data, reducing its reliability and complicating attempts to compare performance. &
    A 2023 KPMG study of 750 companies found that 75\% are in early stages of ESG assurance preparedness, citing frequent data gaps and misaligned metrics. &
    Diminishes trust in ESG disclosures and challenges investors trying to identify genuine ESG leaders vs. potential “greenwashers.” &
    KPMG (2023). Road to Readiness: Risk \& Regulation. \newline
    \url{https://kpmg.com/xx/en/our-insights/risk-and-regulation/road-to-readiness.html} \\

    \rowcolor{tableRow2}
    Absence of uniform verification protocols &
    Without a standardized ESG verification system, data remains uneven across regions, making external assurance inconsistent. &
    Challenges complying with the EU’s CSRD, as firms worldwide are unprepared for more rigorous disclosure and assurance requirements. &
    Harder for analysts to trust disclosed ESG metrics, increasing compliance costs. &
    EU CSRD (2023). \newline
    \url{https://finance.ec.europa.eu/sustainable-finance/disclosures_en} \\

    \rowcolor{tableRow1}
    Varying degrees of transparency and data gaps &
    Some companies and jurisdictions offer very detailed ESG disclosures, while others remain minimal—causing reporting gaps and data blind spots. &
    Hong Kong and Singapore introduced stricter disclosure norms (e.g., ESGenome platform, Project Greenprint) to tackle transparency issues, but uptake varies. &
    Investors can miss significant ESG risks when transparency is lacking or rely on incomplete data, leading to flawed risk assessments. &
    Economist Impact (2024). ESG reporting—challenges for financial services. \newline
    \url{https://impact.economist.com/sustainability/resilience-and-adaptation/esg-reporting-challenges-and-opportunities-for-financial-services-firms} \\

    \rowcolor{tableRow2}
    Different data-gathering formulas by providers &
    ESG rating agencies and data providers weigh E, S, and G factors differently, producing incompatible metrics. &
    Certain rating agencies heavily weight carbon intensity, while others emphasize governance or qualitative factors. &
    Confusion for asset managers trying to evaluate companies consistently; can lead to contradictory ESG “scores.” &
    ESG Rating Disagreement: Implications \ldots (2024). \newline
    \url{https://www.sciencedirect.com/science/article/pii/S1059056024005240} \\

    \rowcolor{tableRow1}
    Lack of universally accepted reporting standard &
    The global ESG landscape hosts multiple frameworks (GRI, SASB, TCFD, ISSB) that are not fully convergent, hindering straightforward comparisons. &
    A 2023 benchmarking study by IFAC noted corporate confusion stemming from the lack of a single global ESG disclosure framework. &
    Forces multinational firms to comply with multiple standards, making data aggregation time-consuming and prone to inconsistencies. &
    IFAC (2023). State of Play in Sustainability Assurance. \newline
    \url{https://www.ifac.org/knowledge-gateway/} \\

    \rowcolor{tableRow2}
    Proprietary methodologies by rating agencies &
    Rating agencies often use opaque or proprietary algorithms to generate ESG scores; companies cannot easily verify how they are calculated. &
    Agency X might track over 300 metrics, including intangible social factors, while Agency Y focuses mostly on carbon footprint and governance frameworks. &
    Investors find it challenging to compare two firms rated by different agencies, creating confusion and skepticism about rating accuracy. &
    The ESG Data Challenge – The Quest \ldots (2023). \newline
    \url{https://aleta.io/knowledge-hub/the-esg-data-challenge} \\

    \rowcolor{tableRow1}
    Rating correlations varying widely among providers &
    Academic research shows correlations between different ESG rating providers can be modest or even negative, confounding investor efforts to benchmark. &
    A study identified negative correlations in certain categories, where one provider’s “high ESG” rating was another’s “low ESG” rating for the same company. &
    Clouds decision-making for investors seeking a straightforward ESG “signal” or consistent corporate ranking. &
    ScienceDirect (2024). \newline
    \url{https://www.sciencedirect.com/science/article/pii/S1059056024005240} \\

    \rowcolor{tableRow2}
    Disagreement on ESG ratings and scores &
    Beyond correlation issues, outright disagreements on a company’s ESG status (high vs. low) complicate capital allocation decisions. &
    Multiple large-cap firms in energy transition have been rated “industry leader” by one agency yet receive below-average ESG ratings from another. &
    Asset managers may invest based on preferential scores or simply aggregate multiple ratings, generating added costs and complexity. &
    Kurz, I. (2024). The Dark Side of ESG Ratings. \newline
    \url{https://www.uni-siegen.de/riskgovernance/dokumente/rg_2024_kurz.pdf} \\

\end{longtable}
}
\end{ThreePartTable}

\subsection{Potential Performance Tradeoffs}
Potential Performance Tradeoffs or Conflicts When Integrating ESG Factors

\noindent 1. Overview of ESG-Related Challenges

Integrating Environmental, Social, and Governance (ESG) considerations into a portfolio can enhance its alignment with sustainability goals and stakeholder values. However, this process occasionally introduces constraints that affect how managers select assets, weigh risks, and balance short-term earnings against longer-term objectives. Although many practitioners view ESG screening and engagement as means to reduce reputational and operational risks, there are times when these strategies generate notable tradeoffs and conflicts.

\noindent \textbf{a. Reduced Investment Universe}  
Stringent ESG criteria or exclusions can narrow the range of eligible assets by steering clear of companies with poorly rated ESG profiles, even if those assets possess attractive financial qualities. The resulting reduction in diversification can concentrate systematic risk within a smaller pool of holdings and may, at times, limit a manager’s ability to capitalize on momentum-driven shifts in particular industries.

\noindent \textbf{b. Divergent Stakeholder Goals}  
Investment mandates, client expectations, and institutional policies may not always align. Some investors want robust returns above all else, while others prioritize the achievement of specific ethical or environmental outcomes. Reconciling these differing goals often forces managers to compromise on pure performance metrics in favor of meeting ESG commitments.

\noindent \textbf{c. Inconsistent Data and Greenwashing}  
Managers depend heavily on third-party ESG ratings or corporate disclosures to form decisions. However, inconsistent methodologies and subjective scoring criteria across rating agencies frequently lead to contradictory assessments of the same company. Additionally, accusations of “greenwashing”—where firms overstate or misrepresent sustainability efforts—can undermine portfolio credibility if holdings later prove to have misleading ESG claims.

\noindent \textbf{d. Potentially Lower Short-Term Gains}  
Allocations intended to advance ESG goals—such as investing in renewable technologies still maturing or in companies transitioning from carbon-intensive processes—sometimes require patience, as their returns may be slow to materialize. In the interim, a portfolio might experience lagging performance relative to peers that focus strictly on near-term profitability.

\noindent 2. Balancing and Mitigating Tradeoffs  
Portfolio managers commonly pursue several strategies to alleviate the conflicts posed by ESG integration. Engaging with companies directly, rather than simply excluding them, can encourage meaningful improvement in ESG practices while preserving valuable investment opportunities. In addition, applying a gradual or tiered approach to ESG thresholds can prevent overly narrow investment universes, helping keep risk-versus-return objectives in focus. Ultimately, researchers and industry practitioners alike emphasize the value of long-term thinking and transparent communication as managers strive to align portfolio performance with evolving sustainability standards.

\subsection{Regulatory Uncertainty}
Impact of Regulatory Uncertainty and Evolving Standards on ESG Investment and Asset Management Strategies

\noindent 1. Regulatory Uncertainty  
Regulatory uncertainty arises when different jurisdictions introduce or revise their frameworks, often with limited coordination between them. This results in shifting compliance thresholds and reporting requirements that can demand significant resources from asset managers. For example, firms operating globally may need to simultaneously adapt to the Sustainable Finance Disclosure Regulation (SFDR) in the European Union while monitoring potential climate-disclosure mandates from the U.S. Securities and Exchange Commission. Such fragmentation raises costs for monitoring and analysis, complicates decision-making, and amplifies risks of both reputational harm and monetary penalties in cases of non-compliance.

– \textit{Risk Management Challenges:} Uncoordinated regulations intensify the complexity of operations, forcing managers to balance differing expectations of stakeholders and regulators.  
– \textit{Costs of Adaptation:} Firms needing to align with multiple regions often invest heavily in research, data platforms, and staff expertise to track developments and update policies ahead of enforcement deadlines.

\noindent 2. Evolving Standards  
Alongside formal regulations, industry-wide standards and best practices continue to evolve, frequently shaped by bodies such as the Task Force on Climate-related Financial Disclosures (TCFD) and the International Sustainability Standards Board (ISSB). As these guidelines become widely accepted, investor and stakeholder expectations also escalate, pushing asset managers to align portfolio strategies with emerging norms.

– \textit{Opportunity for Proactive Firms:} Organizations that integrate forthcoming ESG standards into their planning can strengthen stakeholder trust, attract new clients, and potentially lower compliance costs over the long term.  
– \textit{Transitional Hurdles for Late Adopters:} Entities that delay implementation or take a reactive approach may encounter higher short-term expenditures when new standards become mandatory, as well as a reputational disadvantage compared to proactive peers.

\noindent \textbf{Adapting Strategies}  
\begin{itemize}
  \item \textit{Positioning for Future Rules}: Continuous engagement with regulators—through consultations, comment periods, and direct dialogue—can yield early insights, helping asset managers fine-tune their strategies in anticipation of policy changes.
  \item \textit{Strengthening Compliance Infrastructure}: Investment in specialized software and skilled personnel supports swift reporting, efficient data gathering, and the ability to pivot when new standards emerge.
  \item \textit{Portfolio Diversification}: Spreading investments across various sectors and geographies reduces the chance that regulatory shifts in a single market jeopardize the entire portfolio.
  \item \textit{Active ESG Integration}: Incorporating detailed environmental, social, and governance metrics into risk models and screening processes ensures that investment decisions remain consistent with best practices and keep pace with industry standards.
  \item \textit{Ongoing Education}: Providing frequent training sessions and updates to portfolio managers, research analysts, and operational teams enhances understanding of local and international ESG requirements, thereby promoting agile responses to regulatory developments.
\end{itemize}

By addressing regulatory uncertainty with robust governance processes and aligning with evolving industry standards, asset managers can enhance resilience in their ESG strategies. Such positioning allows them to not only manage risks effectively but also seize opportunities emerging from the global transition toward more sustainable investment practices.

\subsection{Future Growth Hurdles}
Potential Hurdles to Future Growth in ESG Investment and Asset Management

\noindent 1. Data Reliability and Comparability  
Lack of standardized ESG reporting frameworks and frequent data inconsistencies remain at the forefront of challenges. Companies often disclose ESG indicators using varied methodologies, undermining investors’ ability to compare results across sectors and regions. Limited transparency further compounds these problems, and while some jurisdictions (particularly in Europe) continue to refine regulations for more stringent disclosure, fragmented global approaches make it difficult to establish a unified benchmark.

\noindent 2. Climate-Related Volatility and Evolving Metrics  
Climate risk increasingly factors into capital allocation decisions, but it is not always easy to quantify. Investors monitor factors like estimated emissions trajectories and energy transition plans to gauge climate resilience, yet the relevant metrics differ widely across providers and geographies. This patchwork environment can stoke volatility, as changes in climate policies, energy markets, or political sentiment may abruptly shift how investors perceive and price climate-related risks.

\noindent 3. Fragmented Regulatory Landscape  
A lack of alignment in ESG requirements across different regions increases compliance costs and uncertainty. Regulations targeting issues such as greenwashing, mandatory climate disclosures, or standardized reporting vary significantly, and organizations often struggle to reconcile these disparate rules. Firms with proactive, flexible strategies tend to manage these hurdles more effectively, but laggards risk higher capital expenses or reputational setbacks if perceived to fall behind in adapting to emerging requirements.

\noindent 4. Complexities in Thematic and Impact Investing  
In pursuit of more focused ESG goals—like climate adaptation technologies or social equality initiatives—investors turn to thematic and impact strategies. However, the success of these approaches hinges on reliable data and consistent metrics to measure actual impact, which remain works in progress. Even market leaders offering thematic investment solutions (for instance, those centering on resource scarcity or renewable energy) confront uncertainties in translating broad ambitions into tangible, standardized outcome measurements.
\section{Board Oversight of ESG}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{img_search_save/img_search_6.png}
  \caption{\textit{Board oversight of ESG.}}
  \label{fig:primary_image}
\end{figure}

\subsection{The Evolving Role of the Board in ESG Matters}
Below is a concise sub-section illustrating how boards of directors have expanded their oversight role to include ESG issues, alongside recent trends shaping this development.

\textbf{1. Introduction}

Boards of directors have traditionally focused on financial oversight, risk management, and strategic guidance. Increasingly, however, these responsibilities have expanded to encompass environmental, social, and governance (ESG) elements. Whether driven by regulatory shifts, investor expectations, or changing societal values, boards are integrating ESG considerations into broader corporate governance structures to protect stakeholder interests and position their organizations for long-term success.

\textbf{2. Key Drivers of Expanded ESG Oversight}

\textit{a. Heightened Regulatory Expectations}

Across major markets, recent directives (for example, the EU’s Corporate Sustainability Reporting Directive) mandate more stringent sustainability disclosures. These requirements push boards to actively monitor ESG performance, ensuring compliance and reducing legal or reputational risks.

\textit{b. Investor and Stakeholder Demand}

Institutional and retail investors alike increasingly select companies based on ESG credentials. Additionally, stakeholders—ranging from consumers to advocacy groups—scrutinize corporate practices related to climate impacts, diversity, and responsible sourcing. Boards respond by setting transparent ESG goals and implementing formal oversight mechanisms.

\textit{c. Evolving Risk and Strategy Needs}

From supply chain resilience to climate risk resilience, organizations face a growing array of ESG-driven challenges and opportunities. Boards that embed ESG into corporate strategy can more effectively anticipate changes in policy, market preferences, and technology, thus bolstering competitiveness and resilience.

\textbf{3. Recent Trends in Board-Level ESG Oversight}

\textit{a. Specialized ESG Committees}

A growing number of organizations now form dedicated ESG committees. These committees, often led by directors with relevant expertise, work alongside traditional committees (such as audit and risk) to guide ESG priority-setting and track performance against stated targets.

\textit{b. Board Composition and Expertise}

Companies are increasingly recruiting directors with backgrounds in sustainability, social impact, or climate science. The aim is to enrich board-level discussions with up-to-date knowledge of emerging ESG topics and trends, ensuring robust decision-making.

\textit{c. Technology and Data Analytics}

Advances in data analytics make it easier to measure ESG metrics with greater precision. Boards use dashboards and real-time monitoring systems enabled by artificial intelligence to identify risk exposures and performance gaps, facilitating prompt action and informed forecasting.

\textit{d. Heightened Accountability and Transparency}

Regulators and investors are tightening requirements around ESG reporting and disclosure, including third-party assurance on sustainability data. These measures help drive board accountability, reduce incidences of “greenwashing,” and prompt more meaningful discussions on long-term social and environmental impacts.

\subsection{Establishing ESG Committees and Responsibilities}
\textbf{1. Setting Up ESG Committees}

When forming an ESG (Environmental, Social, and Governance) committee, organizations typically begin by establishing a clearly defined charter that outlines the committee’s:
\begin{itemize}
  \item \textit{Mandate}: Identify the key ESG topics most relevant to the company’s operations and stakeholders—such as carbon emissions, supply chain ethics, data protection, or human capital management—along with how the committee intends to address these issues.
  \item \textit{Composition}: Include a balanced mix of independent non-executive directors and subject-matter experts from areas like sustainability, risk management, legal, and finance to achieve perspective diversity and informed decision-making.
  \item \textit{Responsibilities}: Specify the committee’s exact oversight scope, including setting ESG performance objectives, monitoring regulatory updates, guiding business strategy alignment, and collaborating with other board-level committees like audit, compensation, or governance to avoid duplicative efforts.
  \item \textit{Reporting Systems}: Clarify how and when the ESG committee will communicate its findings to the larger board. Quarterly updates or special briefings may be used to ensure that sustainability objectives and progress remain visible at the highest organizational levels.
\end{itemize}

By placing the ESG committee on par with other key committees (e.g., audit, governance, or compensation), companies signal that sustainability and social responsibility considerations carry similar weight in strategic decisions. This integration also helps embed ESG factors in broader corporate risk management and strategic planning processes.

\textbf{2. Accountability within Boards}

After an ESG committee has been established, having robust accountability mechanisms ensures its actions meet intended goals and keep pace with evolving stakeholder expectations. Key practices include:
\begin{itemize}
  \item \textit{Aligned Incentives}: Linking certain executive compensations or bonuses to ESG-related metrics—such as reductions in greenhouse gas emissions or improvements in workforce diversity—helps heighten focus on environmental and social risks.
  \item \textit{Cross-Committee Coordination}: Maintaining open dialogue between the ESG committee and other board committees brings financial and sustainability disclosures into alignment, fostering consistent, data-driven decision-making.
  \item \textit{Third-Party Audits and Assurances}: Independent verification of ESG performance from external specialists provides credibility and transparency, allowing the ESG committee to interpret findings and recommend clear solutions to the board.
  \item \textit{Ongoing Training}: As regulations and stakeholder priorities shift, continuing education empowers both the ESG committee and the broader board to adapt swiftly, remain responsive to new risks and opportunities, and uphold strong oversight of corporate sustainability initiatives.
\end{itemize}

By streamlining reporting, ensuring cross-functional collaboration, and enforcing transparent processes, boards can maintain the authority and credibility of their ESG committees. This emphasis on oversight and accountability underpins sustained performance improvements, fosters trust among investors and the public, and positions the company to address the ever-evolving regulatory and market demands.

\subsection{Aligning Corporate Strategy with ESG Goals}
\textbf{HOW BOARDS INCORPORATE ESG OBJECTIVES INTO BROADER CORPORATE STRATEGY AND LONG-TERM PLANNING}

\textbf{1. INTRODUCTION AND RATIONALE}

Boards across diverse industries increasingly look to embed Environmental, Social, and Governance (ESG) considerations into the broader corporate strategy. This shift is driven by multiple factors, including evolving regulations, heightened investor scrutiny, changing customer expectations, and the recognition that ESG integration can mitigate risk while unlocking new growth opportunities. As the business landscape grows more competitive and transparent, aligning ESG goals with a company’s core strategic vision has become not just a reputational safeguard but also a potential driver of long-term value.

\textbf{2. SUCCESSFUL EXAMPLES OF ESG INTEGRATION}

\begin{itemize}
  \item \textbf{Data-Driven Insights at SEP}: Scottish Equity Partners (SEP) exemplifies a methodical way of integrating ESG by developing a data-driven framework. Their improvements in systematic data collection and alignment with the ESG Data Convergence Initiative showcase how concrete metrics aid in refining strategy and achieving impactful results.
  \item \textbf{Sustainability Focus at IKEA and Google}: IKEA’s concentrated efforts on reducing carbon emissions and expanding renewable energy usage demonstrate the ability to merge social and environmental aims with product innovation. Google, similarly, has pledged to adopt carbon-free energy 24/7 by 2030, aligning sustainability commitments with operational efficiency and brand reputation.
  \item \textbf{Financing the Future via JPMorgan Chase}: A more finance-centric example is JPMorgan Chase’s US\$2.5 trillion commitment to address climate change and sustainable development. This high-level corporate strategy involves directing capital toward renewable energy ventures, signaling to investors and stakeholders the bank’s alignment with broader global ESG goals.
\end{itemize}

\textbf{3. BOARD-LEVEL BEST PRACTICES AND FRAMEWORKS}

\textbf{a. Materiality Assessments:} For any board looking to integrate ESG effectively, starting with a materiality assessment is critical. It pinpoints the most relevant ESG factors that matter to stakeholders, thus guiding strategic priorities.

\textbf{b. SMART Goal Setting:} Boards increasingly adopt Specific, Measurable, Achievable, Relevant, and Time-bound (SMART) goals to translate high-level ambitions into clear, trackable targets. Seeking third-party validation, for instance from the Science-Based Targets Initiative, adds credibility to these goals.

\textbf{c. Established ESG Reporting Frameworks:} Many boards rely on recognized standards and frameworks (e.g., Global Reporting Initiative – GRI; Sustainability Accounting Standards Board – SASB; Task Force on Climate-related Financial Disclosures – TCFD; and Corporate Sustainability Reporting Directive – CSRD) to guide disclosures and facilitate benchmarking. By ensuring consistent measurements and transparent reporting, these frameworks help institutionalize ESG within broader corporate activities.

\textbf{4. REGULATORY INFLUENCES AND RECENT SHIFTS}

Global regulatory developments have also prompted swift changes in board practices. Within the European Union, the CSRD enforces expanded sustainability disclosures, obliging organizations to consider ESG data on par with traditional financial metrics. Enhanced scrutiny of “greenwashing” has resulted in stricter oversight and legal actions, discouraging superficial or misleading claims. Meanwhile, internationally, alignment with the Paris Agreement and increased emphasis on science-based targets demonstrates a rising expectation that companies will structure long-term plans around environmental responsibility.

\textbf{5. CHALLENGES AND OPPORTUNITIES}

Despite the evident benefits, boards can face hurdles such as inconsistent data, fragmented regulations, or initial performance tradeoffs. Yet for organizations embracing ESG, potential advantages include enhanced brand trust, stronger stakeholder relationships, and future-proofed operations in a rapidly shifting market. Boards that integrate ESG into their long-term planning equip their firms to navigate political, climatic, and social uncertainties more adeptly, while also capitalizing on new market niches spawned by green innovation and responsible supply chains.

\subsection{Potential Tensions between Short-Term Returns and Long-Term Sustainability}
\textbf{MANAGING CONFLICTS BETWEEN SHORT-TERM FINANCIAL RETURNS AND LONG-TERM ESG GOALS}

Boards routinely face pressure to deliver immediate earnings while also maintaining a commitment to environmental, social, and governance (ESG) priorities. Striking the right balance can be challenging, requiring diligent oversight, robust frameworks, and a willingness to align incentives with sustainable objectives. Below are key approaches boards use to navigate these tensions:

\begin{itemize}
  \item \textbf{Integrating ESG into Strategic Decisions:} By embedding ESG considerations in long-term strategic planning, directors can identify points where near-term profit targets conflict with broader sustainability goals. A clear articulation of how the company’s financial and ESG commitments intersect allows leaders to anticipate potential reputational or operational risks.
  \item \textbf{Specialized Oversight Mechanisms:} Many boards establish dedicated ESG or sustainability committees to focus on strategy, performance metrics, and reporting. These committees often collaborate with existing risk or audit committees to ensure that short-term decisions do not undermine compliance requirements or stakeholder trust.
  \item \textbf{Aligning Incentives and Compensation:} Tying executive compensation at least partly to ESG targets—such as reduced carbon emissions, supply-chain transparency, or workforce diversity—helps drive behaviors that support both financial results and responsible practices. By incorporating measurable ESG milestones, boards reinforce that sustainability goals are integral to overall performance.
  \item \textbf{Proactive Response to Evolving Regulations:} Recent rules from authorities like the U.S. Securities and Exchange Commission (SEC) and the European Union (EU) increase the transparency expected around climate-related disclosures and social impact. These frameworks effectively compel directors to assess ESG as a core business issue, balancing short-term returns with compliance strategies and stakeholder demands. Forward-looking boards use these guidelines not just to avoid penalties but to capture opportunities in markets that increasingly value sustainability.
  \item \textbf{Continuous Monitoring of Outcomes:} Boards track relevant short-term financial metrics—cash flow, profitability, earnings—and compare them against longer-term ESG indicators, e.g., environmental footprint, social initiatives, or board diversity. This dual focus allows timely adjustments when near-term actions threaten to erode long-term progress.
  \item \textbf{Building a Culture of Accountability:} A culture that prioritizes disclosure and ethical considerations encourages decisions that support both present-day competitiveness and future resilience. Through regular updates to investors, the public, and employees, boards highlight the ways ESG investments foster sustained growth and mitigate risks.
\end{itemize}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{save_viz/plot/plot_6_1.png}
  \caption{\textit{Illustrative data on board ESG oversight prevalence and shareholder support for ESG proposals.}}
  \label{fig:board_esg_bar_chart}
\end{figure}

Below are concise data points related to corporate board ESG oversight and shareholder resolution support:

\begin{itemize}
  \item \textbf{Proportion of Companies with Dedicated ESG Oversight}:
    \begin{itemize}
      \item 54\% of FTSE 100 companies have an ESG-specific board committee.
      \item Among S\&P 500 companies, only 3\% did not disclose ESG board governance in 2022 (down from 14\% the year before).
      \item 15\% of surveyed businesses (according to Deloitte) assign primary ESG oversight to a dedicated sustainability committee.
    \end{itemize}
  \item \textbf{Support for ESG-Related Shareholder Resolutions (U.S., 2024)}:
    \begin{itemize}
      \item Average support for all ESG-focused proposals: 23\%.
      \item Governance proposals: 36\% average support.
      \item Environmental and social proposals: lower support compared to previous years, contributing to a five-year low in well-backed resolutions.
    \end{itemize}
\end{itemize}

\begin{ThreePartTable}
{\fontsize{6pt}{7pt}\selectfont
\renewcommand{\arraystretch}{1.1}
\begin{longtable}{
 L{2.5cm}
 L{5.0cm}
 L{4.0cm}
 L{3.0cm}
}
\caption{\textit{Consolidated overview of ESG drivers, trends, examples, and best practices at the board level.}}
\label{tab:board_esg_table} \\
\toprule
\rowcolor{tableHeader}
\textbf{Theme/Example} & 
\textbf{Overview} & 
\textbf{Board-Level Implication} &
\textbf{Source(s)} \\
\midrule
\endfirsthead

\multicolumn{4}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\
\toprule
\rowcolor{tableHeader}
\textbf{Theme/Example} & 
\textbf{Overview} & 
\textbf{Board-Level Implication} &
\textbf{Source(s)} \\
\midrule
\endhead

\midrule
\multicolumn{4}{r}{{\textit{(Continued on next page)}}} \\
\endfoot

\bottomrule
\endlastfoot

\rowcolor{tableRow1}
1.~Key Driver: Heightened Regulatory Expectations &
Global directives (e.g., EU CSRD) mandate stricter disclosure of ESG metrics, prompting companies to produce transparent, standardized ESG reports. &
Boards must actively monitor compliance to avoid legal/regulatory and reputational risks; they must embed ESG into risk management processes. &
• EU Corporate Sustainability Reporting Directive (CSRD): \url{https://finance.ec.europa.eu/.../corporate-sustainability-reporting_en}
\\

\rowcolor{tableRow2}
2.~Key Driver: Investor \& Stakeholder Demand &
Institutional and retail investors increasingly consider ESG credentials; advocacy groups and consumers scrutinize issues like climate impact. &
Boards should set clear ESG goals, ensure transparent reporting, and align with stakeholder expectations for long-term value creation. &
• Harvard Law School Forum on Corporate Governance (2025)\newline
• EcoActive ESG (2025)
\\

\rowcolor{tableRow1}
3.~Key Driver: Evolving Risk \& Strategy Needs &
Organizations face new ESG risks (supply chain, climate) alongside opportunities (green innovation), requiring adaptive strategies. &
Boards integrating ESG into strategy can anticipate policy and technology shifts, boosting resilience and competitiveness. &
• Russell Reynolds Associates (2025)
\\

\rowcolor{tableRow2}
4.~Recent Trend: Specialized ESG Committees &
Many boards now form dedicated ESG committees with subject-matter experts (risk, legal, finance, sustainability) to guide performance targets. &
Ensures ESG is overseen at the highest levels and not overlooked among traditional finance/risk committees; fosters accountability. &
• OrenNow (2024)\newline
  (Best Practices for Creating an Effective ESG Committee)
\\

\rowcolor{tableRow1}
5.~Recent Trend: Board Composition \& Expertise &
Boards recruit directors with backgrounds in sustainability, social impact, or climate science to enrich discussions and decision-making. &
Brings relevant ESG expertise into board deliberations; improves strategic ESG alignment and effectiveness of oversight. &
• Harvard Law School Forum on Corporate Governance (2021, 2025)
\\

\rowcolor{tableRow2}
6.~Recent Trend: Technology \& Data Analytics &
AI tools, dashboards, and analytics platforms provide real-time ESG data (e.g., carbon emissions, supply chain metrics). &
Allows board members to spot emerging risks and performance gaps, enabling proactive rather than reactive governance. &
• S-RM Inform (2025) ESG Watch
\\

\rowcolor{tableRow1}
7.~Recent Trend: Accountability \& Transparency &
Regulators and investors emphasize third-party assurance of sustainability data, driving more rigorous board oversight and disclosure. &
Boards must ensure robust ESG disclosures, mitigate “greenwashing,” and link ESG outcomes to strategy and reputation management. &
• SEC Climate Disclosure Rules: \url{https://www.sec.gov}
\\

\rowcolor{tableRow2}
8.~Example: IKEA &
Focused on reducing carbon emissions, scaling renewable energy in operations, and embedding sustainability into product design. &
Demonstrates how aligning ESG with product innovation can yield financial benefits and enhanced brand value, requiring board-level commitments. &
• Referenced in the provided text (Step 3).
\\

\rowcolor{tableRow1}
9.~Example: Google &
Commits to carbon-free energy 24/7 by 2030, emphasizes operational efficiency and brand reputation, invests in renewable tech innovation. &
Illustrates how executive support for bold ESG initiatives influences corporate strategy, with the board monitoring progress and risks. &
• Referenced in the provided text (Step 3).
\\

\rowcolor{tableRow2}
10.~Example: JPMorgan Chase &
Devoted US\$2.5 trillion to climate change and sustainable development, showcasing a finance-centric approach. &
Signals that boards can shape capital allocation strategies to address ESG risks/opportunities and meet investor expectations. &
• Referenced in the provided text (Step 3).
\\

\rowcolor{tableRow1}
11.~Example: Scottish Equity Partners (SEP) &
Implemented a systematic, data-driven ESG framework aligned with ESG Data Convergence Initiative to track and benchmark improvements. &
Highlights how measuring and refining ESG metrics can inform strategic decisions at the board level to drive impactful outcomes. &
• SEP’s Data-Driven ESG Strategy:\newline
  \url{https://www.novata.com/.../seps-data-driven-esg-strategy/}
\\

\rowcolor{tableRow2}
12.~Best Practice: Materiality Assessment &
Identifies ESG factors most relevant to a company’s operations and stakeholders (e.g., climate, diversity, product safety). &
Boards use results to set priorities, allocate resources, and design executable strategies aligned with stakeholder concerns. &
• Global Reporting Initiative (GRI): \url{https://www.globalreporting.org}\newline
• Sustainability Accounting Standards Board (SASB): \url{https://www.sasb.org}
\\

\rowcolor{tableRow1}
13.~Best Practice: SMART Goal Setting &
Uses Specific, Measurable, Achievable, Relevant, Time-bound targets (e.g., science-based carbon reduction or diversity benchmarks). &
Ensures ESG ambitions are operational and trackable; boards can measure performance and reward accountable behaviors. &
• Elliott Davis on ESG Goal-Setting:\newline
  \url{https://www.elliottdavis.com/...2025-esg-goal-setting-roadmap}
\\

\rowcolor{tableRow2}
14.~Best Practice: Established ESG Reporting Frameworks &
Aligns disclosures with recognized frameworks (GRI, SASB, TCFD, CSRD) to facilitate consistency, comparability, and investor confidence. &
Standardized reporting credibly demonstrates progress; boards can compare results across peers and track accountability over time. &
• TCFD: \url{https://www.fsb-tcfd.org}\newline
• CSRD: \url{https://ec.europa.eu/.../corporate-sustainability-reporting_en}
\\

\rowcolor{tableRow1}
15.~Challenge \& Opportunity: Ensuring Consistent ESG Data \& Standards &
Boards often face inconsistent methodology, fragmented regulations (global vs. local), and shifting ESG definitions—leading to confusion and “greenwashing” risks. &
Board actions: improve data gathering, unify approaches across jurisdictions, adopt robust third-party assurance, and remain flexible for evolving standards. &
• Russell Reynolds Associates (2025)\newline
• OECD on Corporate Governance: \url{https://www.oecd.org/corporate/}
\\

\end{longtable}
}
\end{ThreePartTable}
\section{Executive Compensation and Accountability}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{img_search_save/img_search_7.png}
  \caption{\textit{Illustration related to executive compensation and accountability}}
  \label{fig:executive_compensation_image}
\end{figure}

\subsection{Linking ESG Metrics to Pay}

\subsubsection{How ESG Metrics Are Embedded}
Companies are increasingly weaving ESG metrics into executive compensation to guide leadership’s focus toward long-term sustainability goals. This is often done by incorporating one or more ESG-related targets into short-term bonuses and long-term incentive plans. For example, scorecards may link a percentage of an executive’s annual bonus to improvements in workplace safety, emissions reduction, or diversity milestones. Although these components frequently comprise a modest share (5\%–15\%) of the total incentive, they serve as a clear signal that sustainability outcomes are priorities at the highest levels. Over time, organizations are moving beyond symbolic gestures to develop more rigorous standards (e.g., verified emission-reduction targets), and many observe that European-based firms and heavily regulated industries—such as energy and utilities—tend to lead the way in applying stricter quantitative benchmarks.

\subsubsection{Which Metrics Are Commonly Used}
\begin{itemize}
\item \textbf{Environmental Metrics:}\\
Carbon footprint (especially greenhouse gas emissions) is a leading measure, particularly for organizations with significant environmental impacts. Some also track resource efficiency, such as water or energy intensity per unit of output.

\item \textbf{Social Metrics:}\\
Diversity, equity, and inclusion (DEI) targets remain prevalent, covering hiring, promotion, or retention rates for underrepresented groups. Workplace safety metrics (e.g., total recordable injury rates) continue to feature in industries where employee well-being is central.

\item \textbf{Governance Metrics:}\\
Aspects of ethical conduct and compliance, while more qualitative, increasingly show up in incentive structures. Some companies link compensation to reducing compliance breaches, strengthening audit processes, or maintaining transparent stakeholder engagement.
\end{itemize}

\subsection{Structures of Performance-Based Compensation}
\textbf{Common Structures of Performance-Based Compensation That Integrate ESG Targets}

\begin{itemize}
\item \textbf{Short-Term Incentives (Annual Bonuses)}\\
  \textit{a. Inclusion of ESG Factors:} Many companies embed measurable ESG objectives—such as carbon intensity reductions, safety improvements, and diversity targets—directly into their annual bonus frameworks. Executives typically receive higher payouts if these sustainability goals are met alongside traditional financial metrics.  
  \textit{b. Targeted Milestones:} Short-term results often center on specific, verifiable milestones (e.g., a percentage decrease in emissions or an increase in employee well-being scores), with clear weightings (like 10–20\% of the annual bonus). If these milestones are validated by internal reviews or independent audits, the bonus component linked to ESG factors is awarded.  
  \textit{c. Blended Approach:} Organizations frequently maintain a blend of financial and non-financial performance indicators in annual scorecards. This approach ensures both profit-focused decisions and responsible business practices—such as improved diversity or ethical supply chain management—are jointly emphasized.

\item \textbf{Long-Term Incentives (Equity and Multi-Year Plans)}\\
  \textit{a. Multi-Year ESG Goals:} These plans often tie equity grants or performance share units to achieving multi-year targets (e.g., a three-to-five-year reduction in carbon footprint). Vesting schedules are contingent on demonstrated progress against the stated ESG benchmarks, encouraging sustained improvements rather than one-time gains.  
  \textit{b. Quantitative Measures and Transparent Benchmarks:} Particularly in Europe, many firms favor numerical ESG goals—like exact cuts in water usage or a targeted board diversity quota—to ensure transparency and objective verification. This helps stakeholders compare performance across companies and aligns with evolving regulatory demands.  
  \textit{c. Governance and Accountability Integration:} Governance-oriented criteria—such as implementing stronger anti-corruption frameworks or achieving certain board independence thresholds—may trigger accelerated vesting or supplemental awards. By formalizing these goals in executive compensation, companies reinforce a culture of responsible oversight and long-term stakeholder value.
\end{itemize}

\subsection{Shareholder Expectations and Disclosure Requirements}

\textbf{How Shareholders Influence ESG-Linked Executive Compensation}\\
Shareholders have gained considerable leverage in shaping executive compensation policies that incorporate Environmental, Social, and Governance (ESG) criteria. The principal mechanism is the “Say on Pay” vote, which offers a clear channel for investors to endorse or challenge a company’s compensation framework. Where disapproval rates run high, boards frequently review how ESG targets are chosen, measured, and integrated into both short- and long-term executive incentives. This mounting pressure has led to an uptick in ESG-linked performance metrics; by 2024, more than three-quarters of S\&P 500 firms reported incorporating factors such as carbon reduction, workforce well-being, or diversity goals into executive pay.

Notably, widespread use of ESG metrics in compensation structures serves two purposes. First, it aligns executive actions with investor priorities by emphasizing sustainable value creation over near-term performance alone. Second, it helps mitigate reputational and financial risks by steering companies away from practices that could invite shareholder activism or proxy battles. Institutional investors, in particular, have ramped up private engagement with boards, pushing beyond simple “yes” or “no” votes to negotiate specific performance thresholds and link vesting schedules or payout multipliers to clearly defined ESG outcomes.

\textbf{Typical Disclosure Requirements and Evolving Best Practices}\\
Regulatory bodies and market expectations increasingly shape disclosure frameworks around ESG-based executive compensation. In the United States, evolving SEC guidelines prompt firms to be transparent about how sustainability targets are determined, measured, and factored into executive pay. This often involves publishing ESG goals—ranging from emissions cuts to workforce diversity—in existing disclosure vehicles like annual proxy statements or compensation committee reports. Shareholders then evaluate whether these goals are sufficiently ambitious and whether payouts accurately reflect ESG achievements.

Global developments reinforce the trend toward granular disclosure. For instance, the EU’s Sustainable Finance Disclosure Regulation (SFDR) urges companies listed in Europe to clarify how sustainability objectives translate into performance-based pay, encouraging comparability across different markets. In practice, many internationally active firms choose to align with various jurisdictions’ requirements to appeal to a broad investor base.

Among recognized best practices:
\begin{itemize}
  \item \textbf{Setting Company-Specific ESG Metrics.} Linking pay to a handful of strategic ESG objectives—rather than generic or overly ambitious benchmarks—helps ensure relevance and accountability.
  \item \textbf{Combining Financial and Non-Financial Indicators.} A balanced scorecard fosters comprehensive leadership oversight, incentivizing long-term stewardship rather than short-term gains.
  \item \textbf{Providing Clear Year-on-Year Comparisons.} Shareholders want evidence of actual progress against previous targets. Transparent metrics and consistent reporting build credibility and mitigate accusations of greenwashing.
  \item \textbf{Early and Constructive Engagement.} Investors increasingly work with boards well before proxy season, discussing proposed ESG metrics and compensation targets in detail to minimize confrontation or “vote no” campaigns.
\end{itemize}

\subsection{Potential Pitfalls and Controversies}

\textbf{1. Greenwashing Risks}\\
Greenwashing typically arises when companies publicly commit to sustainability goals but fall short in delivering tangible results. In the context of executive compensation, this can manifest as boards awarding pay tied to ESG metrics while the underlying initiatives remain largely symbolic. Such discrepancies often involve selective disclosure—publicizing favorable ESG data while omitting other material concerns—and decoupling, which separates the firm’s outward statements from its actual operational changes. These practices can erode stakeholder trust and expose companies to regulatory scrutiny, especially given the growing emphasis on transparent ESG reporting standards. Without rigorous validation of ESG impacts, firms may inadvertently incentivize superficial progress over genuine improvements.

\textbf{2. Misaligned Incentives}\\
Compensation programs can also lead to misaligned incentives if ESG goals are insufficiently defined or conflict with traditional financial metrics. For example, tying short-term bonuses to sustainability targets might drive executives to pursue near-term or superficial “wins” rather than fostering the deeper systemic changes needed for long-term value. If investors perceive that ESG-linked pay fails to align with broader strategic or financial interests, the result may be shareholder dissent. In effect, adopting ESG objectives in pay structures can backfire if boards do not carefully balance these objectives with the company’s overall performance goals.

\textbf{3. Implementation Challenges and Industry Debates}\\
While many organizations are including ESG metrics in executive pay plans, ongoing debates persist about whether these metrics reliably drive shareholder value and broader corporate responsibility. Some critics raise concerns that linking pay to climate or diversity goals may encourage box-ticking rather than holistic, sustainable transformations. Others point out that overseeing ESG performance remains complex, spanning multiple geographies and functional areas—each with its own reporting standards and validation requirements. Consequently, boards and stakeholders might disagree on how best to measure success or how effectively ESG-linked pay supports genuine improvements.

\textbf{4. Regulatory Considerations}\\
Regulatory bodies such as the SEC in the United States and frameworks under the EU Sustainable Finance Disclosure Regulation (SFDR) increasingly require companies to disclose granular ESG data. This push for transparency inevitably puts a spotlight on ESG-linked compensation. When pay is directly tied to environmental or social metrics, boards must demonstrate clear, well-documented criteria and credible verification processes. Legal experts caution that companies failing to align with stricter disclosure rules risk reputational harm and potential liability should reported ESG achievements not match on-the-ground realities.

\textbf{5. Addressing the Pitfalls}\\
To mitigate these challenges, firms can:
\begin{itemize}
  \item \textbf{Clarify ESG Goals:} Adopt standardized, measurable, and independently verifiable ESG metrics to reduce ambiguity and guard against superficial claims.
  \item \textbf{Balance Short- and Long-Term Objectives:} Combine near-term incentives (e.g., annual bonuses) with longer-horizon goals (e.g., three- to five-year targets) to ensure executives prioritize enduring improvements.
  \item \textbf{Ensure Transparent Reporting:} Provide consistent public updates on progress and align with recognized reporting frameworks (e.g., SASB, GRI) to maintain stakeholder trust.
  \item \textbf{Engage Proactively with Shareholders:} Gather and integrate investor feedback to preempt shareholder dissent and ensure that pay programs resonate with broader financial and sustainability expectations.
\end{itemize}

In summary, linking executive compensation to ESG targets holds the promise of driving meaningful social and environmental improvements, but companies must remain vigilant in their design and oversight of such plans. By addressing potential greenwashing, aligning long- and short-term interests, and abiding by emerging regulations, boards can balance shareholder expectations with genuine sustainability outcomes.

\subsection{Additional Data Visualizations}
The following figures illustrate trends in adopting ESG-linked compensation. These data points reflect how companies—across different regions and markets—have committed to integrating ESG targets into executive pay:

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{save_viz/plot/plot_7_1.png}
  \caption{\textit{Bar Chart Comparing ESG-Linked Compensation Percentages}}
  \label{fig:esg_linked_bar}
\end{figure}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{save_viz/plot/plot_7_2.png}
  \caption{\textit{Line Chart Comparing Trends Over Multiple Years}}
  \label{fig:esg_linked_line}
\end{figure}

Recent data suggest a steady upward trajectory in ESG-linked incentives:
\begin{itemize}
  \item S\&P 500 (2021): 66.5\%
  \item S\&P 500 (2023): 75.8\%
  \item Global (2020): 68\%
  \item Global (2022): 77\%
  \item Global (2023): 81\%
  \item Europe (2023): 93\%
  \item U.S. (2023): 76\%
\end{itemize}

\subsection{Example of ESG Integration in Executive Compensation}
\begin{ThreePartTable}
{\fontsize{6pt}{7pt}\selectfont
\renewcommand{\arraystretch}{1.1}
\begin{longtable}{
   L{1.5cm}
   L{2.0cm}
   L{2.2cm}
   L{3.2cm}
   L{4.0cm}
   L{3.5cm}
}
\caption{\textit{Example of ESG Integration in Executive Compensation}}
\label{tab:esg_integration_example} \\
\toprule
\rowcolor{tableHeader}
\textbf{Company Name} & \textbf{Types of ESG Metrics Used} & \textbf{Integration into Compensation} & \textbf{Percentage of Compensation Linked to ESG} & \textbf{Observed Outcomes or Benefits} & \textbf{Industry Trends} \\
\midrule
\endfirsthead

\multicolumn{6}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\
\toprule
\rowcolor{tableHeader}
\textbf{Company Name} & \textbf{Types of ESG Metrics Used} & \textbf{Integration into Compensation} & \textbf{Percentage of Compensation Linked to ESG} & \textbf{Observed Outcomes or Benefits} & \textbf{Industry Trends} \\
\midrule
\endhead

\midrule
\multicolumn{6}{r}{{\textit{(Continued on next page)}}} \\
\endfoot

\bottomrule
\endlastfoot

\rowcolor{tableRow1}
Enel Group &
Safety, Emissions Reductions, Climate Goals &
Short-term and Long-term Incentives &
Not publicly specified, but integral to both plans &
Pursues decarbonization (80\% CO\textsubscript{2} reduction by 2030), fosters workplace safety, and aligns with $1.5^\circ\mathrm{C}$ scenario &
European utilities typically lead in stricter quantitative ESG benchmarks \\

\end{longtable}
}
\end{ThreePartTable}
\section{Shareholder Activism and ESG}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{img_search_save/img_search_8.png}
  \caption{\textit{Illustrative overview of ESG-focused shareholder activism.}}
  \label{fig:primary_image_section8}
\end{figure}

\subsection{Role of Activist Investors in Driving ESG Change}

Below is a concise but comprehensive explanation of how shareholder activism has evolved to incorporate Environmental, Social, and Governance (ESG) considerations, along with typical methods activist investors use.

1. Historical Context and Expansion into ESG  
\begin{itemize}
  \item Early Foundations: In the early 20th century, shareholder activism primarily addressed financial and governance matters, especially in the United States after the 1929 market crash led to the formation of the Securities and Exchange Commission (SEC).  
  \item Shift in the 1970s: Inspired by socially minded organizations, activists began submitting proposals on topics such as civil rights, fair labor practices, and health and safety. Groups like the Interfaith Center on Corporate Responsibility demonstrated the power of combining ethical considerations with shareholder rights.  
  \item Governance Movement in the 1980s: Activism focused on senior leadership structures, executive compensation, and keeping boards accountable. Around this time, environmental activism entered the conversation—propelled by the Coalition for Environmentally Responsible Economies (CERES)—signaling the early integration of ESG considerations.  
  \item Modern Developments: Over the past two decades, shareholders have increasingly sought meaningful sustainability metrics from companies, pushing disclosure standards to include climate impacts, diversity, and long-term social risks. Regulatory changes, such as the introduction of universal proxy cards in the U.S., now enable more direct participation in board nominations, aiding activist efforts to champion ESG reforms.
\end{itemize}

2. Key ESG Concerns for Activist Shareholders  
\begin{itemize}
  \item Environmental Issues  
    – Climate disclosures: Many proposals center on transparent reporting of Scope 1, 2, and 3 emissions.  
    – Binding obligations: In certain jurisdictions, particularly in Europe, activists pursue legally enforceable environmental commitments, including net-zero transition plans and science-based targets.
  \item Social Issues  
    – Worker welfare: Labor rights, wages, and workplace safety are prominent factors, especially during economic instability.  
    – Diversity and inclusion: Shareholders routinely call for more inclusive hiring practices, equitable pay, and culturally responsive governance.
  \item Governance and Anti-ESG  
    – Board accountability: Investors seek independent, informed boards that integrate ESG into broader risk and strategy planning.  
    – Counter-movements: Anti-ESG initiatives have emerged, questioning whether companies should devote resources to ESG obligations.
\end{itemize}

3. Typical Methods Used by Activist Investors  
\begin{itemize}
  \item Direct Engagement  
    – Dialogue and negotiation: Investors propose specific targets or ESG metrics, fostering collaborative solutions before resorting to formal proxy activity.
  \item Shareholder Resolutions and Proxy Voting  
    – Proxy campaigns: When engagement fails, shareholders may file resolutions or nominate board candidates who advocate for ESG reforms.  
    – Universal proxy: A recent shift in U.S. proxy rules allows shareholders to more freely choose among both company-endorsed and activist-endorsed nominees.
  \item Coalition Building and Public Campaigns  
    – Collective pressure: Activists frequently join forces with NGOs, advocacy groups, or other investors to file joint resolutions, raising public awareness and intensifying reputational pressure on companies.  
    – Media and stakeholder outreach: By amplifying issues through press coverage, activists expand scrutiny of corporate ESG shortcomings.
\end{itemize}

4. Conclusion  
Shareholder activism has evolved from a narrow concentration on financial returns and governance best practices to at least partially embracing holistic ESG considerations. Influential investors argue that addressing environmental and social risks ultimately supports long-term corporate stability and success. Though tensions between pro-ESG and anti-ESG factions continue, activist momentum toward meaningful environmental impact, employee welfare, and responsible governance shows no sign of slowing.

\begin{ThreePartTable}
{\fontsize{6pt}{7pt}\selectfont
\renewcommand{\arraystretch}{1.1}
\begin{longtable}{
    L{2.2cm}
    L{5.0cm}
    L{3.2cm}
    L{3.0cm}
    L{3.0cm}
}
    \caption{\textit{Evolution of Shareholder Activism}} \label{tab:evolution_shareholder_activism}\\

    \rowcolor{tableHeader}
    \textbf{Time Period} & \textbf{Key Milestone or Event} & \textbf{Major Organization(s)} & \textbf{ESG Focus Areas} & \textbf{Significance} \\
    \endfirsthead

    \multicolumn{5}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\
    \rowcolor{tableHeader}
    \textbf{Time Period} & \textbf{Key Milestone or Event} & \textbf{Major Organization(s)} & \textbf{ESG Focus Areas} & \textbf{Significance} \\
    \endhead

    \endfoot

    \endlastfoot

    \rowcolor{tableRow1}
    1930s–1940s &
    \begin{tabular}[l]{@{}l@{}}• Post-1929 market crash and formation of the SEC\\• Early governance measures in U.S. corporate\end{tabular} &
    SEC (Securities and Exchange Commission) &
    Initial emphasis on financial accountability and governance &
    Created regulatory groundwork for future shareholder activism \\
    
    \rowcolor{tableRow2}
    1950s–1960s &
    \begin{tabular}[l]{@{}l@{}}• Howard Bowen’s “Social Responsibilities of the \\  Businessman” (1953) highlights moral obligations\\• Heightened social activism (civil rights, Vietnam War)\end{tabular} &
    \begin{tabular}[l]{@{}l@{}}N/A (early corporate social\\ responsibility advocates)\end{tabular} &
    Broader “corporate social responsibility” rather than formal ESG &
    Sparked early discussions on corporate responsibility beyond pure profit \\
    
    \rowcolor{tableRow1}
    1970s &
    \begin{tabular}[l]{@{}l@{}}• Emergence of shareholder proposals on civil rights, \\ health, and safety\\• Start of “ethical” investment strategies\end{tabular} &
    Interfaith Center on Corporate Responsibility (ICCR) &
    Early social factors, especially labor practices and health/safety &
    Demonstrated the power of ethically driven shareholder initiatives \\
    
    \rowcolor{tableRow2}
    1980s &
    \begin{tabular}[l]{@{}l@{}}• Governance movement focusing on executive \\  compensation, board structures\\• Environmental activism gains traction\end{tabular} &
    Coalition for Environmentally Responsible Economies (CERES) &
    Introduction of environmental considerations into activism &
    Integrated environmental elements into traditional governance activism \\
    
    \rowcolor{tableRow1}
    1990s &
    Rising public awareness of global environmental issues, corporate accountability &
    \begin{tabular}[l]{@{}l@{}}CERES, NGO coalitions\end{tabular} &
    Continued environmental focus, plus governance &
    Shift from purely financial activism to broader ESG agenda \\
    
    \rowcolor{tableRow2}
    2000s &
    \begin{tabular}[l]{@{}l@{}}• Increased pressure for climate disclosures, diversity\\  reporting, and ethical supply chains\\• Large institutional investors heighten ESG demands\end{tabular} &
    \begin{tabular}[l]{@{}l@{}}Multiple investor coalitions;\\ large institutional investors\end{tabular} &
    Climate, diversity, and long-term social risk disclosure &
    ESG metrics become common in annual reports, with growing influence of institutional investors \\
    
    \rowcolor{tableRow1}
    2010s–Present &
    \begin{tabular}[l]{@{}l@{}}• Universal proxy rules enable broader board involvement\\• Surge in both pro-ESG and anti-ESG proposals\\• Regulatory moves (e.g., CSRD, stricter SEC oversight)\end{tabular} &
    \begin{tabular}[l]{@{}l@{}}Various activists, including\\ pro- and anti-ESG groups\end{tabular} &
    Full integration: environmental, social, and governance issues &
    ESG fully enters mainstream investor discourse; ESG proposals increasingly shape board composition and strategy \\
\end{longtable}
}
\end{ThreePartTable}

\subsection{Influence of Proxy Voting and Resolutions}

Proxy voting refers to the process by which shareholders delegate their voting power to a representative, typically via proxy ballots. This enables both institutional and retail investors to steer corporate decision-making without needing to attend annual or special meetings in person. In an ESG context, these votes often center on governance matters—such as board composition or executive remuneration—as well as environmental and social issues. Consequently, shareholder voices can be expressed on topics like climate impact, workforce diversity, and ethical supply chain standards.

Shareholder resolutions, meanwhile, are proposals submitted for a vote among all shareholders. Though generally non-binding in many jurisdictions (for instance, the United States), these resolutions can significantly influence corporate agendas. Companies frequently engage with shareholders when resolutions are introduced, and even those that fail to reach majority support may trigger internal discussions or expanded disclosures on ESG metrics.

1. Pushing ESG Agendas Through Active Engagement and Examples  
\begin{itemize}
  \item Communication Channel for ESG Priorities: By proposing resolutions and voting on existing proposals, investors articulate ESG priorities directly to company boards and management teams. Leading investment firms such as BlackRock and State Street annually release guidelines highlighting climate risk management, board diversity, and political engagement.  
  \item Notable Cases Demonstrating ESG Impact:  
    – Climate Action at Oil Majors: Oil and gas giants have faced resolutions demanding specific emissions reduction targets, often prompting management to alter sustainability tactics and provide more frequent climate disclosures.  
    – Board Diversity Initiatives: Investors have introduced proposals calling for reports on board composition and inclusive governance practices. Rising levels of support have accelerated the recruitment of diverse directors.  
    – Linking Executive Pay to ESG Performance: Several proposals advocate incorporating environmental or social goals into executive compensation structures, spurring companies to factor ESG into pay practices.
\end{itemize}

2. Evolving Trends and Regulatory Considerations  
\begin{itemize}
  \item Intensified Shareholder Activism: Forecasts for the 2025 proxy season suggest sector-specific ESG demands, covering areas like data security in technology or labor practices in retail.  
  \item Regulatory Requirements: The U.S. Securities and Exchange Commission (SEC) sets thresholds and oversees the eligibility of shareholder proposals, while the European Union imposes country-specific but robust engagement rules.  
  \item Influence Beyond Voting Outcomes: Even when proposals fall short of majority support, a strong showing can prompt companies to expand sustainability commitments, issue ESG disclosures, or pursue broader changes in governance.
\end{itemize}

\subsection{Notable Activism Campaigns}

High-profile ESG activist campaigns underscore the growing wave of activity aimed at holding companies accountable for their environmental, social, and governance impacts. Groups such as Follow This and ClientEarth have focused on urging large corporates to adopt more ambitious climate goals, while anti-ESG proposals have also arisen, challenging the role of ESG in corporate strategy.

1. Outcomes and Lessons Learned  
\begin{itemize}
  \item Settlements and Board Changes: Many ESG campaigns concluded through negotiated settlements, compelling firms to strengthen sustainability metrics or replace board members with individuals who possess related expertise.  
  \item Multi-Activist “Swarm” Tactics: Activists frequently collaborate, focusing especially on climate and diversity issues. Companies that offer transparent disclosure and a clear sustainability strategy tend to fare better.  
  \item Balancing Divergent Stakeholders: Firms increasingly face opposing proposals on environmental targets or diversity policies. Effective communication across the investor base—including both ESG-driven and traditional investors—can mitigate conflict and support long-term strategy.
\end{itemize}

\subsection{Future Outlook of ESG Activism}

ESG-focused activism is experiencing rapid evolution, driven by stricter regulations, shifting investor expectations, and broader international collaboration. While traditional activism often centered on short-term financial goals, today’s activists emphasize sustainability metrics, community engagement, and improved governance. Looking ahead, several trends stand out:

1. Regulatory Changes  
\begin{itemize}
  \item Expanded Disclosure Rules: Authorities (e.g., the SEC, the EU’s Corporate Sustainability Reporting Directive) require detailed climate and sustainability data, enabling activists to identify ESG performance gaps.  
  \item Anti-Greenwashing Measures: Governments worldwide are imposing stricter requirements to ensure corporate sustainability claims are verifiable and aligned with accurate metrics.
\end{itemize}

2. Investor Attitudes  
\begin{itemize}
  \item Growing Emphasis on Climate Action: Major institutional investors recognize climate risk as core to portfolio management, supporting enhanced ESG metrics and corporate accountability.  
  \item Persistent Skepticism in Some Segments: Certain investor contingents still question the linkage between ESG and financial returns, requiring activists to present strong data on performance benefits and risk mitigation.  
  \item Preference for Pragmatic Collaboration: Investors increasingly seek constructive dialogues, partnering with companies to develop feasible ESG goals rather than applying blanket exclusions.
\end{itemize}

3. Global Collaboration  
\begin{itemize}
  \item Transnational Initiatives: Coalitions like Climate Action 100+ unite institutional investors globally to push high-emission companies on carbon reduction strategies.  
  \item Harmonized Standards: Bodies like the International Organization for Standardization (ISO) and the Global Sustainable Investment Alliance (GSIA) are developing common benchmarks, helping activists coordinate efforts.  
  \item Multilateral Support and Learning: Cross-border alliances facilitate knowledge-sharing on effective ESG campaigns, expanding the reach and impact of activist demands.
\end{itemize}

4. Outlook  
\begin{itemize}
  \item Greater Data-Driven Accountability: Standardized reporting will allow activists to pinpoint performance gaps and press companies for measurable improvements.  
  \item Robust Public Scrutiny: Tighter legal frameworks against greenwashing embolden activists to highlight incomplete or misleading ESG claims.  
  \item Strengthened International Networks: Collaboration across regions and sectors increasingly amplifies activist efforts, potentially shaping business strategies to integrate environmental stewardship, social responsibility, and governance best practices.
\end{itemize}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{save_viz/plot/plot_8_1.png}
  \caption{\textit{Trends in ESG-Related Shareholder Proposals and Success Rates (2021--2024)}}
  \label{fig:esg_trends}
\end{figure}


\section{References}
\subsection{ESG Integration in Portfolio Selection}
\begin{itemize}
  \item \href{https://www.robeco.com/en-us/glossary/sustainable-investing/best-in-class}{Robeco – Best in Class}
  \item \href{https://www.spglobal.com/esg/csa}{Dow Jones Sustainability Indices (S\&P Global)}
  \item \href{https://corpgov.law.harvard.edu/2022/08/08/does-esg-negative-screening-work}{Harvard Law School Forum on Corporate Governance – “Does ESG Negative Screening Work?”}
  \item \href{https://knowesg.com/featured-article/7-best-esg-investment-strategies-to-integrate-into-your-portfolio}{KnowESG – “ESG Investment Strategies”}
  \item \href{https://www.unpri.org/introductory-guides-to-responsible-investment/an-introduction-to-responsible-investment-screening-and-exclusions/12727.article}{UN PRI – “Screening and Exclusions”}
  \item \href{https://www.msci.com/indexes/category/esg-indexes}{MSCI ESG Indexes}
  \item \href{https://en.wikipedia.org/wiki/Dow_Jones_Sustainability_Indices}{Dow Jones Sustainability Indices – Wikipedia}
  \item \href{https://www.spglobal.com/spdji/en/indices/sustainability/dow-jones-best-in-class-world-index/}{S\&P Global – Dow Jones Best-in-Class World Index}
  \item \href{https://www.msci.com/documents/1296102/51277550/2025+Sustainability+and+Climate+Trends+Paper.pdf}{MSCI’s 2025 Sustainability and Climate Trends Paper}
  \item \href{https://www.msci.com/esg-ratings}{MSCI ESG Ratings}
  \item \href{https://www.sustainalytics.com/esg-ratings}{Sustainalytics ESG Ratings}
  \item \href{https://hr.bloombergadria.com/data/files/Pitanja%20i%20odgovori%20o%20Bloomberg%20ESG%20Scoreu.pdf}{Bloomberg ESG Scores}
  \item \href{https://kpmg.com/au/en/home/insights/2021/10/closing-gap-in-esg-data-quality.html}{KPMG \& Google Cloud: “Closing the gap in ESG data quality”}
  \item \href{https://www.rsm.global/service/esg-and-sustainability-services/third-party-verification-reporting}{RSM Global: Third-Party Verification and Reporting}
  \item \href{https://doi.org/10.1080/20430795.2015.1118917}{Friede, G., Busch, T., \& Bassen, A. (2015). ESG and financial performance. \textit{Journal of Sustainable Finance \& Investment}}
  \item \href{https://www.researchgate.net/publication/371417188_ESG_and_Sustainable_Finance_A_Critical_Review_of_the_Influence_of_ESG_Scores_on_Firm%27s_Performance}{Chilukuri, N. (2023). ESG and Sustainable Finance: A Critical Review}
  \item \href{https://thesis.eur.nl/pub/69971/MSc-Thesis-Sjoerd-Ebbing-484123-.pdf}{Ebbing, S. (2023). A multi-factor analysis on ESG metrics. Erasmus School of Economics.}
  \item \href{http://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2024-Lisbon/papers/ESGScreeningInvesting011524.pdf}{Agapova, A., Filatova, U., \& Yuk, I. (2024). Positive versus negative ESG portfolio screening. EFMA Annual Meeting Paper}
  \item \href{https://www.morganstanley.com/ideas/sustainable-funds-performance-2023-full-year}{Morgan Stanley – “Sustainable Funds Outperformed Peers in 2023”}
\end{itemize}
\subsection{Thematic and Impact Investing Approaches}
\begin{itemize}
  \item \href{https://ca.rbcwealthmanagement.com/documents/369152/369168/ESG+-+What+is+Thematic+ESG+Investing.pdf}{RBC Wealth Management, “What is Thematic ESG Investing?”}
  \item \href{https://www.unpri.org/investment-tools/thematic-and-impact-investing}{UNPRI, “Thematic and Impact Investing”}
  \item \href{https://www.schwab.com/learn/story/what-is-thematic-investing}{Charles Schwab, “What is Thematic Investing?”}
  \item \href{https://www.blackrock.com/us/individual/insights/thematic-investing}{BlackRock, “Thematic Investing”}
  \item \href{https://www.globalreporting.org/}{Global Reporting Initiative (GRI)}
  \item \href{https://www.sasb.org/}{Sustainability Accounting Standards Board (SASB)}
  \item \href{https://www.fsb-tcfd.org/}{Task Force on Climate-related Financial Disclosures (TCFD)}
  \item \href{https://ec.europa.eu/info/business-economy-euro/company-reporting-and-auditing/company-reporting/corporate-sustainability-reporting_en}{Corporate Sustainability Reporting Directive (CSRD)}
  \item \href{https://www.tesla.com/impact}{Tesla Impact Report}
  \item \href{https://global.toyota/en/sustainability/}{Toyota Global Sustainability}
  \item \href{https://www.jpmorgan.com/insights/investing/investment-strategy/alternative-investments-in-2025-our-top-five-themes-to-watch}{J.P. Morgan (2025). Alternative Investments in 2025: Our Top Five Themes to Watch}
  \item \href{https://thegiin.org/impact-investor-survey/}{The GIIN (2025). Impact Investor Survey}
  \item \href{https://www.mofo.com/resources/insights/250203-2025-esg-sustainability-predictions}{Morrison Foerster (2025). 2025 ESG + Sustainability Predictions}
  \item \href{https://corpgov.law.harvard.edu/2025/02/03/ceo-and-c-suite-esg-priorities-for-2025/}{Harvard Law School Forum on Corporate Governance (2025). CEO and C-Suite ESG Priorities for 2025}
  \item \href{https://www.investopedia.com/}{Investopedia on Thematic ETFs}
  \item \href{https://www.blackrock.com/us/financial-professionals/investments/products/thematic-etfs}{BlackRock’s Thematic ETF Insights}
  \item \href{https://www.jpmorgan.com/insights/global-research/investing/etf-guide}{J.P. Morgan’s ETF Market Guide}
  \item \href{https://www.ishares.com/us/insights/flow-and-tell-recap-2024}{iShares Flow \& Tell Recap 2024}
  \item \href{https://kuvera.in/blog}{Kuvera’s Analysis of Sectoral/Thematic Fund Performance}
\end{itemize}
\subsection{Measuring ESG-linked Returns}
\begin{itemize}
\item \href{https://corpgov.law.harvard.edu/2025/01/07/esg-performance-metrics-in-executive-compensation-strategies/}{Harvard Law School Forum on Corporate Governance (2025). “ESG Performance Metrics in Executive Compensation Strategies.”}
\item \href{https://www.skadden.com/insights/publications/2025/01/esg-a-review-of-2024-and-key-trends-to-look-for-in-2025}{Skadden, Arps, Slate, Meagher \& Flom LLP (2025). “ESG: A Review of 2024 and Key Trends To Look for in 2025.”}
\item \href{https://www.oecd.org/content/dam/oecd/en/publications/reports/2025/02/behind-esg-ratings_4591b8bb/3f055f0c-en.pdf}{OECD (2025). “Behind ESG Ratings: Unpacking Sustainability Metrics.”}
\item \href{https://www.msci.com/esg-metrics}{MSCI. “ESG Metrics.”}
\item \href{https://www.sustainalytics.com/esg-ratings}{Sustainalytics. “ESG Risk Ratings.”}
\item \href{https://www.researchgate.net/publication/381111776_ESG_Investing_A_Statistically_Valid_Approach_to_Data-Driven_Decision_Making_and_the_Impact_of_ESG_Factors_on_Stock_Returns_and_Risk}{ESG Investing: A Statistically Valid Approach to Data-Driven Decision Making and the Impact of ESG Factors on Stock Returns and Risk. ResearchGate.}
\item \href{https://link.springer.com/article/10.1007/s10462-024-10708-3}{Environmental, Social, and Governance (ESG) and Artificial Intelligence in Finance: State-of-the-Art and Research Takeaways. Springer.}
\item \href{https://www.mirova.com/sites/default/files/2023-01/our-approach-to-esg-assessment_2023.pdf}{Our Approach to Impact and ESG Assessment, Mirova.}
\item \href{https://www.stern.nyu.edu/sites/default/files/assets/documents/NYU-RAM_ESG-Paper_2021%20Rev_0.pdf}{NYU Stern (2021). ESG AND FINANCIAL PERFORMANCE: Uncovering the Relationship by Aggregating Evidence from 1,000 Plus Studies.}
\item \href{https://clsbluesky.law.columbia.edu/2023/03/08/do-the-old-rules-apply-to-esg-ratings-and-benchmarks/}{CLS Blue Sky Blog (2023). Do the Old Rules Apply to ESG Ratings and Benchmarks?}
\item \href{https://www.investopedia.com/terms/b/benchmark.asp}{Investopedia. Benchmarks: Definition, Types, and How to Use Them in Investing.}
\item \href{https://www.unpri.org/pri-blog/part-iii-esg-factors-and-returns-a-review-of-recent-research/12728.article}{UNPRI – “Part III: ESG factors and returns – a review of recent research.”}
\item BNY Mellon Women’s Opportunities ETF (BKWO) and Franklin Responsibly Sourced Gold ETF (FGDL) (Market performance data as of 2025).
\item \href{https://ecohumanism.co.uk/joe/ecohumanism/article/view/6342/6480}{Journal of Ecohumanism – “The Impact of ESG Factors on Investment Decisions: Exploring the Interplay Between Sustainability Reporting, Corporate Governance, and Financial Performance.”}
\item \href{https://cameronacademy.com/the-financial-impact-of-esg-tools-on-investment-portfolios-an-in-depth-review/}{Cameron Academy – “The Financial Impact of ESG Tools on Investment Portfolios: An In-depth Review.”}
\item \href{https://jemi.edu.pl/vol-21-issue-1-2025/does-esg-performance-have-an-impact-on-financial-performance-evidence-from-turkey}{JEMI – “Does ESG performance have an impact on financial performance? Evidence from Turkey.”}
\end{itemize}
\subsection{ESG Product Innovation}
\begin{itemize}
  \item \href{https://www.fool.com/investing/stock-market/types-of-stocks/esg-investing/esg-bonds/}{The Motley Fool: ESG Bonds}
  \item \href{https://www.icmagroup.org/assets/documents/Regulatory/Green-Bonds/LMASustainabilityLinkedLoanPrinciples-270919.pdf}{International Capital Market Association (ICMA): Sustainability Linked Loan Principles}
  \item \href{https://www.rbcgam.com/en/ca/learn-plan/types-of-investments/what-are-esg-etfs/detail}{RBC Global Asset Management: ESG ETFs}
  \item \href{https://www.morningstar.com/lp/global-esg-flows}{Morningstar (Global ESG Flows Report)}
  \item \href{https://www.globenewswire.com/news-release/2025/03/14/3042794/0/en/}{Globe Newswire. (2025, March 14). “Trends \& Strategies Shaping the \$2.58 Trillion Sustainable Finance Industry, 2025-2030.”}
  \item \href{https://www.rbccm.com/}{RBC Capital Markets. (2024). “Global ESG Fixed Income Investor Survey.”}
  \item \href{https://www.sustainalytics.com/}{Sustainalytics. (2025). “Top-Rated Companies.”}
  \item \href{https://www.bloomberg.com/professional/products/indices/esg-climate/}{Bloomberg. (n.d.). “ESG \& Climate Indices.”}
  \item \href{https://www.msci.com/indexes/category/esg-indexes}{MSCI. (n.d.). “ESG Indexes.”}
  \item \href{https://www.keyesg.com/article/your-need-to-know-summary-of-esg-regulations-and-frameworks}{Key ESG – EU ESG Regulations}
  \item \href{https://plana.earth/academy/eu-esg-regulations}{Plan A – EU ESG Regulations Overview}
  \item \href{https://www.pwc.com/us/en/services/esg/library/sec-climate-disclosures.html}{PwC – Guidance on SEC Climate Disclosures}
  \item \href{https://www.unpri.org/policy/us-policy/sec-esg-related-disclosure}{UN PRI – SEC ESG-Related Disclosure}
  \item \href{https://sdgs.un.org/goals}{United Nations Sustainable Development Goals}
  \item \href{https://www.cliffordchance.com/insights/thought_leadership/trends/2023/esg-trends-2023.html}{Clifford Chance (2023). ESG Trends 2023}
  \item \href{https://www.morganstanley.com/content/dam/msdotcom/en/assets/pdfs/Morgan_Stanley_2023_ESG_Report.pdf}{Morgan Stanley (2024). 2023 ESG Report}
  \item \href{https://www.sciencedirect.com/science/article/pii/S0301479723025963}{ScienceDirect (2024). The Inclusion of Biodiversity into ESG Framework.}
  \item \href{https://www2.deloitte.com/content/dam/insights/us/articles/5073_Advancing-ESG-investing/DI_Advancing-ESG-investing_UK.pdf}{Deloitte (2023). Advancing ESG Investing}
  \item \href{https://natlawreview.com/article/esg-blockchain-and-ai-oh-my}{The National Law Review (2023). AI and Blockchain Technologies Benefit Company ESG Reporting.}
\end{itemize}
\subsection{Challenges in ESG Investment \& Asset Management}
\begin{itemize}
  \item \href{https://www.uni-siegen.de/riskgovernance/dokumente/rg_2024_kurz.pdf}{Kurz, I. (2024). “The Dark Side of ESG Ratings – Reliability and Challenges.”}
  \item \href{https://www.sciencedirect.com/science/article/pii/S1059056024005240}{ESG Rating Disagreement: Implications and Aggregation Approaches. (2024). ScienceDirect.}
  \item \href{https://aleta.io/knowledge-hub/the-esg-data-challenge}{The ESG Data Challenge – The Quest for Quality Data. (2023). Aleta.}
  \item \href{https://www.sganalytics.com/blog/esg-data-challenges/}{ESG Data Challenges in Data Accessibility \& Quality. (2025). SG Analytics.}
  \item \href{http://www.lse.ac.uk/fmg}{Edmans, A., Gosling, T., \& Jenter, D. (2025). “Sustainable Investing: Evidence From the Field.” Financial Markets Group Discussion Paper No. 920.}
  \item \href{https://ijrpr.com/uploads/V6ISSUE3/IJRPR39734.pdf}{Tulasi, G.V.N.L.S. \& Vedala, N.S. (2025). “The Effect of ESG Factors on Portfolio Construction: A Strategic Approach to Sustainable Investing.” International Journal of Research Publication and Reviews, 6(3), 1482–1484.}
  \item \href{https://www.researchgate.net/publication/389790274_Investors'_Standpoint_Developing_Climate_Finance-Oriented_Investment_Strategies}{Galloppo, G. (2025). “Investors’ Standpoint: Developing Climate Finance-Oriented Investment Strategies.” In \textit{A Journey into ESG Investments} (pp. 107–133). Springer.}
  \item \href{https://finance.ec.europa.eu/sustainable-finance/disclosures_en}{European Commission – Sustainable Finance Disclosure Regulation (SFDR).}
  \item \href{https://www.sec.gov/rules/proposed/2022/33-11042.pdf}{U.S. Securities and Exchange Commission – Proposed Climate Disclosure Rule.}
  \item \href{https://www.fsb-tcfd.org/}{Task Force on Climate-related Financial Disclosures (TCFD).}
  \item \href{https://www.ifrs.org/issb/}{International Sustainability Standards Board (ISSB) – IFRS Foundation.}
  \item \href{https://www.msci.com/research-and-insights/2023-esg-climate-trends-to-watch}{MSCI, “ESG and Climate Trends to Watch for 2023.”}
  \item \href{https://www.morganstanley.com/ideas/sustainable-investing-trends-outlook-2023}{Morgan Stanley, “Sustainable Investing Trends: Outlook 2023.”}
  \item \href{https://www.blackrock.com/corporate/literature/continuous-disclosure-and-important-information/tcfd-report-2023-blkinc.pdf}{BlackRock, “2023 TCFD Report.”}
  \item \href{https://www.blackrock.com/sg/en/investment-strategies/megatrends-and-thematic-investing}{BlackRock, “Megatrends \& Thematic Investing.”}
  \item \href{https://kpmg.com/xx/en/our-insights/risk-and-regulation/road-to-readiness.html}{KPMG (2023). Road to Readiness: Risk \& Regulation.}
  \item \href{https://impact.economist.com/sustainability/resilience-and-adaptation/esg-reporting-challenges-and-opportunities-for-financial-services-firms}{Economist Impact (2024). ESG reporting—challenges and opportunities for financial-services firms.}
  \item \href{https://www.ifac.org/knowledge-gateway/}{IFAC (2023). State of Play in Sustainability Assurance.}
  \item \href{https://www.jpmorgan.com/insights/investing/investment-strategy/alternative-investments-in-2025-our-top-five-themes-to-watch}{J.P. Morgan (2025). Alternative Investments in 2025: Our Top Five Themes to Watch.}
  \item \href{https://thegiin.org/impact-investor-survey/}{The GIIN (2025). Impact Investor Survey.}
  \item \href{https://www.mofo.com/resources/insights/250203-2025-esg-sustainability-predictions}{Morrison Foerster (2025). 2025 ESG + Sustainability Predictions.}
  \item \href{https://corpgov.law.harvard.edu/2025/02/03/ceo-and-c-suite-esg-priorities-for-2025/}{Harvard Law School Forum on Corporate Governance (2025). CEO and C-Suite ESG Priorities for 2025.}
  \item \href{https://www.msci.com/esg-ratings}{MSCI ESG Ratings.}
  \item \href{https://www.sustainalytics.com/esg-ratings}{Sustainalytics ESG Ratings.}
  \item \href{https://hr.bloombergadria.com/data/files/Pitanja%20i%20odgovori%20o%20Bloomberg%20ESG%20Scoreu.pdf}{Bloomberg ESG Scores.}
  \item \href{https://kpmg.com/au/en/home/insights/2021/10/closing-gap-in-esg-data-quality.html}{KPMG \& Google Cloud: “Closing the gap in ESG data quality.”}
  \item \href{https://www.rsm.global/service/esg-and-sustainability-services/third-party-verification-reporting}{RSM Global: Third-Party Verification and Reporting.}
\end{itemize}
\subsection{Board Oversight of ESG}
\begin{itemize}
  \item Harvard Law School Forum on Corporate Governance (2025). Thoughts for Boards: Key Issues in Corporate Governance for 2025.
  \item Russell Reynolds Associates (2025). Global Corporate Governance Trends for 2025. \url{https://www.russellreynolds.com/en/insights/reports-surveys/}
  \item EcoActive ESG (2025). The Role of Board Oversight in ESG – A 2025 Perspective.
  \item Harvard Law School Forum on Corporate Governance (2021). ESG Governance: Board and Management Roles \& Responsibilities. \url{https://corpgov.law.harvard.edu/2021/11/10/esg-governance-board-and-management-roles-responsibilities/}
  \item Moss Adams (2024). ESG Board Committee Frameworks. \url{https://www.mossadams.com/articles/2024/09/esg-board-committees-frameworks}
  \item S-RM Inform (2025). ESG Watch | March 2025. \url{https://www.s-rminform.com/esg-watch/esg-watch-march-2025}
  \item OrenNow (2024). Best Practices for Creating an Effective ESG Committee. \url{https://www.orennow.com/blog/best-practices-for-creating-an-effective-esg-committee}
  \item SEP’s Data-Driven ESG Strategy: \url{https://www.novata.com/resources/case-studies/seps-data-driven-esg-strategy/}
  \item Elliott Davis on ESG Goal-Setting: \url{https://www.elliottdavis.com/insights/the-ultimate-2025-esg-goal-setting-roadmap}
  \item ESG Strategy Examples (Apiday): \url{https://www.apiday.com/blog-posts/top-esg-strategy-examples-for-a-sustainable-business-model}
  \item Wharton ESG Case Studies: \url{https://esg.wharton.upenn.edu/centers-labs/esg-case-studies/}
  \item Global Reporting Initiative (GRI): \url{https://www.globalreporting.org/}
  \item Sustainability Accounting Standards Board (SASB): \url{https://www.sasb.org/}
  \item Task Force on Climate-related Financial Disclosures (TCFD): \url{https://www.fsb-tcfd.org/}
  \item Corporate Sustainability Reporting Directive (CSRD): \url{https://ec.europa.eu/info/business-economy-euro/banking-and-finance/sustainable-finance/corporate-sustainability-reporting_en}
  \item Paris Agreement: \url{https://www.un.org/en/climatechange/paris-agreement}
  \item Harvard Law School Forum on Corporate Governance: \url{https://corpgov.law.harvard.edu/}
  \item OECD on Corporate Governance: \url{https://www.oecd.org/corporate/}
  \item SEC (U.S.) Climate Disclosure Rules: \url{https://www.sec.gov/}
  \item EU Corporate Sustainability Reporting Directive: \url{https://finance.ec.europa.eu/capital-markets-union-and-financial-markets/company-reporting-and-auditing/company-reporting/corporate-sustainability-reporting_en}
\end{itemize}
\subsection{Executive Compensation and Accountability}
\begin{itemize}
  \item [1.] Forbes (2025, February 5). Executive Compensation For ESG Metrics: A Step In The Right Direction But Still A Long Way To Go.  
  \url{https://www.forbes.com/sites/hecparis/2025/02/05/executive-compensation-for-esg-metrics-a-step-in-the-right-direction-but-still-a-long-way-to-go/}

  \item [2.] WTW (2025, February). Organizations Shift Focus On ESG Executive Incentive Metrics – From Prevalence To Quality.  
  \url{https://www.wtwco.com/en-au/insights/2025/02/organizations-shift-focus-on-esg-executive-incentive-metrics-from-prevalence-to-quality}

  \item [3.] Harvard Law School Forum on Corporate Governance. “ESG Performance Metrics in Executive Compensation Strategies.”  
  \url{https://corpgov.law.harvard.edu/2025/01/07/esg-performance-metrics-in-executive-compensation-strategies/}

  \item [4.] WTW. “Global Report on ESG Metrics in Incentive Plans 2023.”  
  \url{https://www.wtwco.com/en-ch/insights/2024/01/global-report-on-esg-metrics-in-incentive-plans-2023}

  \item [5.] Debevoise \& Plimpton. (2024). 2025 Executive Compensation Reminders for Public Companies.  
  \url{https://www.debevoise.com/insights/publications/2024/12/2025-executive-compensation-reminders-for-public}

  \item [6.] Harvard Law School Forum on Corporate Governance. (2025). 2025 Proxy Season Preview.  
  \url{https://corpgov.law.harvard.edu/2025/03/10/2025-proxy-season-preview/}

  \item [7.] Sustainalytics. (n.d.). Say on Pay: CEO Compensation and the Long Tail of Shareholder Dissent.  
  \url{https://www.sustainalytics.com/esg-research/resource/investors-esg-blog/say-on-pay--ceo-compensation-and-the-long-tail-of-shareholder-dissent}

  \item [8.] WTW (2025). “Investor Perspectives on ESG Metrics in Executive Incentive Programs.”  
  \url{https://www.wtwco.com/en-mu/insights/2025/03/investor-perspectives-on-esg-metrics-in-executive-incentive-programs}

  \item [9.] ScienceDirect (2024). “Quantifying Firm-Level Greenwashing: A Systematic Literature Review.”  
  \url{https://www.sciencedirect.com/science/article/pii/S0301479724033851}

  \item [10.] Harvard Law School Forum on Corporate Governance (2025). “ESG Performance Metrics in Executive Compensation Strategies.”  
  \url{https://corpgov.law.harvard.edu/2025/01/07/esg-performance-metrics-in-executive-compensation-strategies/}

  \item [11.] Cleary Gottlieb (2025). “A New Regulatory Environment for Climate and Other ESG Reporting Rules.”  
  \url{https://www.clearygottlieb.com/news-and-insights/publication-listing/a-new-regulatory-environment-for-climate-and-other-esg-reporting-rules}

  \item [12.] Harvard Law School Forum on Corporate Governance (2024). “ESG Performance Metrics in Executive Pay.”  
  \url{https://corpgov.law.harvard.edu/2024/01/15/esg-performance-metrics-in-executive-pay/}

  \item [13.] ESG Today (2024). “More than 80\% of Companies Adopting ESG Metrics in Exec Compensation Plans.”  
  \url{https://www.esgtoday.com/more-than-80-of-companies-adopting-esg-metrics-in-exec-compensation-plans-wtw-study/}

  \item [14.] Candriam (2023). “The State of Pay: ESG Metrics in Executive Remuneration.”  
  \url{https://www.candriam.com/siteassets/medias/insights/esg/the-state-of-pay-esg-metrics-in-executive-remuneration/2023_05_wp_esg_metrics_gb.pdf}
\end{itemize}
\subsection{Shareholder Activism and ESG}
\begin{itemize}
  \item [1.] FTI Consulting (2023). “Shareholder Activism on ESG Matters: The 2023 Proxy Season Experience.”  
        \href{https://fticommunications.com/shareholder-activism-on-esg-matters-the-2023-proxy-season-experience/}{Link}
  \item [2.] Harvard Law School Forum on Corporate Governance (2023). “The Evolving Battlefronts of Shareholder Activism.”  
        \href{https://corpgov.law.harvard.edu/2023/03/28/the-evolving-battlefronts-of-shareholder-activism/}{Link}
  \item [3.] Harvard Law School Forum on Corporate Governance (2023). “Anti-ESG Shareholder Proposals in 2023.”  
        \href{https://corpgov.law.harvard.edu/2023/06/01/anti-esg-shareholder-proposals-in-2023/}{Link}
  \item [4.] Interfaith Center on Corporate Responsibility.  
        \href{https://www.iccr.org/}{Link}
  \item [5.] SEC Official Website.  
        \href{https://www.sec.gov/}{Link}
  \item [6.] ClimeCo: “The ABCs of Proxy Voting and Its Role in ESG.”  
        \href{https://www.climeco.com/insights-library/the-abcs-of-proxy-voting-and-its-role-in-esg/}{Link}
  \item [7.] Diligent Insights: “ESG Proxy Voting \& How It’s Shaping the Boardroom.”  
        \href{https://www.diligent.com/resources/blog/esg-proxy-voting}{Link}
  \item [8.] Harvard Law School Forum on Corporate Governance (2025). “2025 Proxy Season Preview.”  
        \href{https://corpgov.law.harvard.edu/2025/03/10/2025-proxy-season-preview/}{Link}
  \item [9.] Glass Lewis (2025). “2025 Shareholder Proposals \& ESG Benchmark Policy Guidelines.”  
        \href{https://resources.glasslewis.com/hubfs/2025%20Guidelines/2025%20Shareholder%20Proposals%20%26%20ESG%20Benchmark%20Policy%20Guidelines.pdf}{Link}
  \item [10.] UN Principles for Responsible Investment: “Trends and Challenges in Sustainability-Related Shareholder Resolutions.”  
        \href{https://www.unpri.org/stewardship/trends-and-challenges-in-sustainability-related-shareholder-resolutions/12968.article}{Link}
  \item [11.] Harvard Law School Forum on Corporate Governance (2025). “Shareholder Activism 2024 Review and 2025 Outlook.”  
        \href{https://corpgov.law.harvard.edu/2025/03/14/shareholder-activism-2024-review-and-2025-outlook/}{Link}
  \item [12.] IR Impact (2025): “The Times They Are a-Changin’: The New Era of Institutionalized Shareholder Activism.”  
        \href{https://www.ir-impact.com/2025/01/the-times-they-are-a-changin-the-new-era-of-institutionalized-shareholder-activism/}{Link}
  \item [13.] Slaughter and May (2025). “2025 Activism Playbook: Trends, Expectations, and Corporate Preparedness.”  
        \href{https://www.slaughterandmay.com/horizon-scanning-2025/crisis-management-2025/2025-activism-playbook-trends-expectations-and-corporate-preparedness/}{Link}
  \item [14.] The Conference Board (2025). “2025 Proxy Season.”  
        \href{https://www.conference-board.org/press/2025-proxy-season-preview}{Link}
  \item [15.] BNP Paribas. (2023). “ESG Global Survey 2023.”  
        \href{https://securities.cib.bnpparibas/app/uploads/sites/3/2023/12/esg-global-survey-consolidated-report.pdf}{Link}
  \item [16.] Deutsche Bank. (2023). CIO Special ESG Survey 2023.
  \item [17.] Climate Action 100+. (n.d.).  
        \href{https://www.climateaction100.org/}{Link}
  \item [18.] ISO. (2024). “ESG Implementation Principles Launch.”  
        \href{https://www.iso.org/news/2024/11/esg-implementation-principles-launch}{Link}
  \item [19.] Global Sustainable Investment Alliance. (n.d.).  
        \href{https://www.gsi-alliance.org/}{Link}
  \item [20.] U.S. Securities and Exchange Commission. (2024). “Climate Disclosure Rules (SEC).”  
        \href{https://www.sec.gov/}{Link}
  \item [21.] European Commission. (n.d.). “Corporate Sustainability Reporting.”  
        \href{https://finance.ec.europa.eu/sustainable-finance/disclosure-and-reporting/corporate-sustainability-reporting_en}{Link}
  \item [22.] Harvard Law School Forum on Corporate Governance (2025). “Activism in the 2024 Proxy Season.”  
        \href{https://corpgov.law.harvard.edu/2025/03/14/activism-in-the-2024-proxy-season-and-implications-for-2025/}{Link}
  \item [23.] FTI Consulting (2023).  
        \href{https://fticommunications.com/shareholder-activism-on-esg-matters-the-2023-proxy-season-experience/}{Link}
  \item [24.] Harvard Law School Forum on Corporate Governance (2023–2024).  
        \href{https://corpgov.law.harvard.edu/}{Link}
  \item [25.] The Sustainable Agency (2024). “The History of ESG.”  
        \href{https://thesustainableagency.com/blog/the-history-of-esg/}{Link}
\end{itemize}



\end{document}
"""

succes_bool, emsg = create_pdf_from_latex(latex_code, "save_reports/output_report_new.pdf") #, True)
print("######################")
print("succes_bool : ",succes_bool)
print("emsg : ",emsg)
