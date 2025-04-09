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
                  # "lualatex",
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
                # "-xelatex",
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

\title{The Rise of Decentralized Finance (DeFi) and Its Challenges to Traditional Banking Models and Regulation}
\author{}
\date{}

\begin{document}
\maketitle
\tableofcontents

\section{Introduction to Decentralized Finance (DeFi)}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{img_search_save/img_search_1.png}
  \caption{\textit{Representation of DeFi Concept}}
  \label{fig:defi_concept_image}
\end{figure}

Decentralized Finance (commonly referred to as DeFi) refers to a blockchain-based ecosystem where traditional financial services—such as lending, borrowing, trading, and earning interest—are delivered through smart contracts and decentralized protocols rather than through centralized intermediaries like banks. This approach aims to offer faster settlement times, lower transaction fees, and broader access to financial products for anyone with an internet connection.

\subsection{Context and Definition}

\textbf{Context.}
\begin{itemize}
  \item \textbf{Rapid Market Growth:} Since around 2020, DeFi has witnessed substantial increases in both user adoption and total value locked (TVL) in various protocols. Recent estimates indicate that the overall market size is projected to grow significantly over the next decade, driven by innovations in decentralized exchanges, lending platforms, and token-based financial products.
  \item \textbf{Openness and Accessibility:} Most DeFi platforms operate permissionlessly, allowing global participants to transact or even build new financial tools. This inclusivity can foster financial innovation and accessibility, though it also introduces challenges concerning user protection and compliance.
  \item \textbf{Regulatory Considerations:} Policymakers around the world are assessing DeFi’s implications for investor safety, market integrity, and taxation. Official reports propose that broad standards and frameworks may be needed to address security gaps and regulatory uncertainties.
\end{itemize}

\textbf{Definition.}  
DeFi predominantly operates on blockchain networks like Ethereum, which utilize self-executing smart contracts. Because these automated contracts can replace traditional intermediaries, users can access financial services with fewer barriers. While this setup reduces dependence on centralized institutions, it also hinges on strong smart contract design and network security.

\subsection{Brief Evolution}
\begin{itemize}
  \item \textbf{Foundations with Bitcoin (2009):} Bitcoin introduced the concept of decentralized money, proving that peer-to-peer transactions are possible without conventional banking channels.
  \item \textbf{Expansion via Ethereum (2015):} Ethereum’s launch enabled programmable smart contracts, paving the way for sophisticated decentralized applications. Early DeFi initiatives utilized Ethereum’s flexibility to pioneer open lending, yield strategies, and decentralized exchange protocols.
  \item \textbf{Emergence of Stablecoins and DEXs:} The rise of stablecoins—cryptocurrencies pegged to external assets—coupled with user-oriented decentralized exchanges (e.g., Uniswap) significantly boosted market liquidity and trading volumes. By mitigating volatility concerns and simplifying on-chain swaps, stablecoins fostered broader DeFi participation.
  \item \textbf{Future Directions:} Enhancements such as Layer-2 scaling solutions and decentralized autonomous organizations (DAOs) are moving DeFi toward greater efficiency and resilience. Regulatory developments, strengthened security measures, and more intuitive user experiences are poised to further shape the sector.
\end{itemize}

\begin{ThreePartTable}
{\fontsize{6pt}{7pt}\selectfont
\renewcommand{\arraystretch}{1.1}
\begin{longtable}{
  L{3.0cm}
  L{8.0cm}
  L{3.0cm}
}
    \caption{\textit{Overview of Key DeFi Market Metrics and Regulatory Insights (2020--2023)}} \label{tab:defi_overview} \\
    \toprule
    \rowcolor{tableHeader}
    \textbf{Aspect} & \textbf{Details} & \textbf{Source} \\
    \midrule
    \endfirsthead

    \multicolumn{3}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\
    \toprule
    \rowcolor{tableHeader}
    \textbf{Aspect} & \textbf{Details} & \textbf{Source} \\
    \midrule
    \endhead

    \midrule
    \multicolumn{3}{r}{{\textit{(Continued on next page)}}} \\
    \endfoot

    \bottomrule
    \endlastfoot

    \rowcolor{tableRow1}
    Market Size (2023) &
    Estimated at around USD 14.35 billion &
    Global Market Insights (2023) \\

    \rowcolor{tableRow2}
    Projected Growth (2024--32) &
    Expected CAGR of over 46.8\% &
    Global Market Insights (2023) \\

    \rowcolor{tableRow1}
    Total Value Locked (TVL) &
    Increased from roughly USD 10 billion in 2020 to over USD 50 billion by 2023 &
    Statista; Global Market Insights (2023) \\

    \rowcolor{tableRow2}
    Regulatory Recommendations &
    Nine policy suggestions focusing on market integrity, investor protection, and compliance &
    IOSCO (2023) \\

    \rowcolor{tableRow1}
    Barriers to Adoption &
    Complexity of user interfaces and the technical knowledge required to use DeFi platforms &
    Global Market Insights (2023) \\

    \rowcolor{tableRow2}
    Role of DAOs &
    DAOs growing as key governance structures, enabling decentralized decision-making &
    Innowise, sector reports \\
\end{longtable}
}
\end{ThreePartTable}

\section{Foundational Concepts and Architecture of DeFi}

\begin{figure}[H]
  \centering
  \includegraphics[width=1.0\textwidth]{img_search_save/img_search_2.png}
  \caption{\textit{An illustrative representation of decentralized finance architecture.}}
  \label{fig:defi_foundations}
\end{figure}

\subsection{Blockchain and Smart Contracts}
\textbf{Blockchain.} Blockchain underpins most decentralized finance applications by providing a decentralized ledger where all transactions, balances, and records are securely verified. Unlike traditional banking databases controlled by a central authority, blockchain networks rely on consensus algorithms (such as Proof of Work or Proof of Stake) to confirm transaction accuracy. This approach ensures transparency, reduces reliance on intermediaries, and can lower operating costs. Advances in cryptography and block design have steadily improved scalability, enabling DeFi systems to handle a growing volume of transactions while maintaining security and robustness.

\textbf{Smart Contracts.} Smart contracts are programmable codes, hosted on blockchain networks, that automatically execute the terms of an agreement when predefined conditions are met. They reduce or eliminate the need for traditional legal intermediaries, thereby shortening execution timelines and minimizing the risk of human error. For example, a lending platform smart contract might release loan proceeds automatically once collateral has been verified. By automating intricate processes and offering transparent auditing trails, smart contracts enable efficient and trust-minimized financial services in the decentralized economy.

\subsection{Role of Governance Tokens}
Governance tokens distribute decision-making power among a project’s community of users, developers, and investors. Holders of these tokens can vote on proposals affecting protocol parameters, treasury allocations, or partnership initiatives. This democratic governance model promotes decentralized control, aligning the interests of a broad participant base with the project’s growth and security. By granting token holders a tangible voice in the system’s evolution, governance tokens cultivate a level of community engagement rarely seen in traditional finance, where decision-making typically remains centralized.

\subsection{Cross-Chain Solutions}
In the early stages of decentralized finance, many initiatives were isolated on specific blockchains, limiting how users could deploy assets across different ecosystems. Cross-chain solutions address these constraints by enabling distinct blockchains to communicate and share data. Bridging protocols facilitate token transfers between networks, while interoperability layers allow applications to query and validate information from multiple blockchains. As the need for greater flexibility continues to grow, cross-chain solutions pave the way toward a more unified global financial infrastructure, ensuring that resources and data can flow more freely among various decentralized platforms.

\subsection{Implications for Traditional Banking and Regulation}
By demonstrating that core financial activities—such as lending, trading, and payments—can run autonomously through transparent code, decentralized finance reveals significant new possibilities in efficiency and accessibility. In contrast, traditional banking systems rely heavily on intermediaries and centralized oversight. This shift introduces complexities for regulators, as DeFi’s decentralized nature often spans multiple jurisdictions and lacks single points of control. At the same time, DeFi opens opportunities for broader financial inclusion and innovation, stimulating dialogue between technology pioneers, legacy financial institutions, and policymakers. Crafting balanced regulatory frameworks that ensure safety, market stability, and fair practices while still promoting creativity could be a key factor in integrating decentralized finance solutions into mainstream commerce.


\end{document}
\section{References}
\subsection{Introduction to Decentralized Finance (DeFi)}
\begin{itemize}
  \item \href{https://kpmg.com/mc/en/home/insights/2023/07/newsletter-advisory-decentralized-finance.html}{KPMG on DeFi Advisory}
  \item \href{https://www.gminsights.com/industry-analysis/decentralized-finance-defi-market}{Global Market Insights}
  \item \href{https://www.iosco.org/library/pubdocs/pdf/ioscopd754.pdf}{IOSCO (2023) Regulatory Report}
  \item \href{https://www.investopedia.com/decentralized-finance-defi-5113835}{Investopedia Reference on DeFi}
  \item \href{https://innowise.com/blog/defi-in-banking/}{Innowise on DeFi in Banking}
  \item \href{https://hedera.com/learning/decentralized-finance/defi-trends}{Hedera on Key DeFi Trends}
  \item \href{https://www.statista.com/statistics/1272181/defi-tvl-in-multiple-blockchains/}{Statista (DeFi TVL Data)}
\end{itemize}

\subsection{Foundational Concepts and Architecture of DeFi}
\begin{itemize}
  \item Tripathi, G. (2023). “A comprehensive review of blockchain technology: Underlying principles and historical background with future challenges.” ScienceDirect. \href{https://www.sciencedirect.com/science/article/pii/S2772662223001844}{Descriptive Link}
  \item Smart Contract – an overview. ScienceDirect. \href{https://www.sciencedirect.com/topics/computer-science/smart-contract}{Descriptive Link}
  \item Unlocking Benefits: The Role of Governance Tokens in Cryptocurrency and DeFi. (2024). BlockApps. \href{https://blockapps.net/blog/unlocking-benefits-the-role-of-governance-tokens-in-cryptocurrency-and-defi/}{Descriptive Link}
  \item Cross-Chain Solutions: The Future of DeFi. Nextrope. \href{https://nextrope.com/the-future-of-decentralized-finance-interoperability-and-cross-chain-solutions/}{Descriptive Link}
  \item The Impact of Decentralized Finance on Traditional Banking. Openware. \href{https://www.openware.com/news/articles/the-impact-of-decentralized-finance-on-traditional-banking/}{Descriptive Link}
  \item Deloitte’s Global Blockchain Survey (publicly available on Deloitte’s website)
  \item PR Newswire reports regarding cross-chain solution market analysis
\end{itemize}


\end{document}
"""

succes_bool, emsg = create_pdf_from_latex(latex_code, "save_reports/output_report_new_lua.pdf") #, True)
print("######################")
print("succes_bool : ",succes_bool)
print("emsg : ",emsg)
