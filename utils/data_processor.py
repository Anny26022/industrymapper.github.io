import pandas as pd
from typing import List, Tuple, Dict
from collections import defaultdict

class IndustryMapper:
    def __init__(self):
        """Initialize the mapper with the permanent backend database."""
        try:
            self.load_database()
        except Exception as e:
            raise Exception(f"Failed to load industry mapping database: {str(e)}")

    def load_database(self):
        """Load the permanent industry mapping database."""
        try:
            # Load industry categories
            industry_categories = pd.read_csv('attached_assets/Industry Analytics.csv', header=None)
            self.available_industries = sorted(industry_categories[0].unique())

            # Load symbol mappings from the complete dataset
            stock_data = pd.read_csv('attached_assets/Basic RS Setup (4).csv')
            self.mapping_df = pd.DataFrame({
                'symbol': stock_data['Stock Name'],
                'industry': stock_data['Basic Industry']
            })

            # Validate industries in mapping against available categories
            invalid_industries = set(self.mapping_df['industry']) - set(self.available_industries)
            if invalid_industries:
                raise ValueError(f"Invalid industries in mapping: {invalid_industries}")

            self.mapping_dict = dict(zip(
                self.mapping_df['symbol'].str.upper(),
                self.mapping_df['industry']
            ))
        except FileNotFoundError:
            raise Exception("Industry mapping database not found")
        except Exception as e:
            raise Exception(f"Error reading industry database: {str(e)}")

    def clean_symbols(self, symbols: str) -> List[str]:
        """Clean and validate input symbols."""
        # Split and clean symbols
        symbols = symbols.replace('\n', ',').replace(';', ',')
        
        # Process symbols, removing any "NSE:" prefix if present
        symbol_list = []
        for s in symbols.split(','):
            if s.strip():
                # Remove NSE: prefix if present
                clean_symbol = s.strip().upper()
                if clean_symbol.startswith("NSE:"):
                    clean_symbol = clean_symbol[4:]
                symbol_list.append(clean_symbol)

        # Remove duplicates while preserving order
        seen = set()
        symbol_list = [x for x in symbol_list if not (x in seen or seen.add(x))]

        return symbol_list

    def map_symbols(self, symbols: str) -> Tuple[Dict[str, str], List[str]]:
        """Map symbols to industries and return mapping and invalid symbols."""
        clean_symbol_list = self.clean_symbols(symbols)

        if len(clean_symbol_list) > 999:
            raise ValueError("Maximum 999 symbols allowed per batch")

        mapped_symbols = {}
        invalid_symbols = []

        for symbol in clean_symbol_list:
            if symbol in self.mapping_dict:
                mapped_symbols[symbol] = self.mapping_dict[symbol]
            else:
                invalid_symbols.append(symbol)

        return mapped_symbols, invalid_symbols

    def format_tv_output(self, mapped_symbols: Dict[str, str]) -> str:
        """Format the output in TradingView compatible format with industry grouping."""
        # Group symbols by industry
        industry_groups = defaultdict(list)
        for symbol, industry in mapped_symbols.items():
            industry_groups[industry].append(symbol)

        # Format output with industry grouping
        # Sort industries by number of symbols in descending order
        formatted_lines = []
        sorted_industries = sorted(industry_groups.items(), key=lambda x: len(x[1]), reverse=True)
        for industry, symbols in sorted_industries:
            symbol_count = len(symbols)
            nse_symbols = [f"NSE:{symbol}" for symbol in sorted(symbols)]
            formatted_line = f"###{industry}({symbol_count}),{','.join(nse_symbols)}"
            formatted_lines.append(formatted_line)

        return ",".join(formatted_lines)
        
    def format_flat_output(self, mapped_symbols: Dict[str, str]) -> str:
        """Format the output as a flat list of symbols without industry grouping."""
        # Just list all symbols with NSE: prefix
        nse_symbols = [f"NSE:{symbol}" for symbol in sorted(mapped_symbols.keys())]
        return ",".join(nse_symbols)

    def get_available_industries(self) -> List[str]:
        """Get list of all available industries in the database."""
        return self.available_industries

    def get_fundamentals_data(self, symbols: List[str]) -> pd.DataFrame:
        """Get fundamentals data for the given symbols."""
        try:
            # Load results calendar data
            results_df = pd.read_csv('attached_assets/Results Calendar.csv')
            
            # Convert all symbols to uppercase
            results_df['Stock Name'] = results_df['Stock Name'].str.upper()
            symbols = [symbol.upper() for symbol in symbols]
            
            # Filter for the requested symbols
            filtered_df = results_df[results_df['Stock Name'].isin(symbols)]
            
            if filtered_df.empty:
                return pd.DataFrame()
            
            # Rename columns for better readability
            column_mapping = {
                'Stock Name': 'Symbol',
                'Quarterly Results Date': 'Results Date',
                'QoQ % Net Profit Latest': 'QoQ Net Profit %',
                'QoQ % EPS Latest': 'QoQ EPS %',
                'YoY% EPS Latest': 'YoY EPS %',
                'QoQ % Sales Latest': 'QoQ Sales %',
                'YoY % Sales Latest': 'YoY Sales %'
            }
            
            filtered_df = filtered_df.rename(columns=column_mapping)
            
            # Convert date format if needed (DD/MM/YYYY to more readable format)
            try:
                filtered_df['Results Date'] = pd.to_datetime(filtered_df['Results Date'], format='%d/%m/%Y')
                filtered_df['Results Date'] = filtered_df['Results Date'].dt.strftime('%d %b %Y')
            except:
                pass  # Keep original format if conversion fails
                
            return filtered_df
        except Exception as e:
            print(f"Error fetching fundamentals data: {str(e)}")
            return pd.DataFrame()

    def get_database_stats(self) -> Dict[str, int]:
        """Get statistics about the mapping database."""
        return {
            'total_symbols': len(self.mapping_df),
            'total_industries': len(self.available_industries),
            'mapped_industries': len(self.mapping_df['industry'].unique())
        }