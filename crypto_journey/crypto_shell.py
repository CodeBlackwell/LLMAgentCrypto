#!/usr/bin/env python
"""
Crypto Trading Shell - A minimalist CLI shell for crypto trading strategies.
"""
import cmd
import sys
import os
import json
import datetime
from colorama import Fore, Style, init

# For crypto trading
from lumibot.entities import Asset
from lumibot.backtesting import CcxtBacktesting

# Initialize colorama
init(autoreset=True)

class CryptoShell(cmd.Cmd):
    """Simple command processor for crypto trading."""
    
    intro = f"""{Fore.CYAN}
    ╔═══════════════════════════════════════════════╗
    ║  {Fore.YELLOW}Crypto Trading Shell v0.1{Fore.CYAN}                   ║
    ║  Type 'help' or '?' to list commands.         ║
    ║  Type 'exit' or 'quit' to exit.              ║
    ╚═══════════════════════════════════════════════╝
    """
    prompt = f'{Fore.GREEN}crypto> {Style.RESET_ALL}'
    
    # Trading configuration
    config = {
        'exchange': 'coinbase',
        'strategy': 'random',
        'coin': 'BTC',
        'quote': 'USD',
        'cash_at_risk': 0.25,
        'start_date': '2023-06-01',
        'end_date': '2023-12-31',
        'min_timestep': 'day'
    }
    
    # Available exchanges and strategies
    available_exchanges = ['coinbase', 'kraken', 'binance', 'bitfinex']
    available_strategies = ['random', 'sma_crossover', 'rsi_strategy', 'sentiment_based']
    
    # ----- basic commands -----
    def do_exit(self, arg):
        """Exit the shell."""
        print(f"{Fore.YELLOW}Goodbye!")
        return True
        
    def do_quit(self, arg):
        """Exit the shell."""
        return self.do_exit(arg)
        
    def do_help(self, arg):
        """List available commands with "help" or detailed help with "help cmd"."""
        if arg:
            # Show help about a specific command
            super().do_help(arg)
        else:
            # Show custom help menu
            print(f"{Fore.CYAN}Available commands:")
            print(f"{Fore.GREEN}help{Style.RESET_ALL} - Show this help message")
            print(f"{Fore.GREEN}quit, exit{Style.RESET_ALL} - Exit the shell")
            print(f"{Fore.GREEN}version{Style.RESET_ALL} - Show version information")
            print(f"{Fore.YELLOW}\nTrading Commands:")
            print(f"{Fore.GREEN}list_exchanges{Style.RESET_ALL} - List available exchanges")
            print(f"{Fore.GREEN}list_strategies{Style.RESET_ALL} - List available trading strategies")
            print(f"{Fore.GREEN}show_config{Style.RESET_ALL} - Show current configuration")
            print(f"{Fore.GREEN}set_parameter <name> <value>{Style.RESET_ALL} - Set configuration parameter")
            print(f"{Fore.GREEN}save_config <filename>{Style.RESET_ALL} - Save configuration to file")
            print(f"{Fore.GREEN}load_config <filename>{Style.RESET_ALL} - Load configuration from file")
            print(f"{Fore.GREEN}run_backtest{Style.RESET_ALL} - Run backtest with current configuration")
            
    def do_version(self, arg):
        """Show version information."""
        print(f"{Fore.CYAN}Crypto Trading Shell v0.1")
        print(f"Running on Python {sys.version.split()[0]}")
    
    # ----- trading commands -----
    def do_list_exchanges(self, arg):
        """List available exchanges."""
        print(f"{Fore.CYAN}Available exchanges:")
        for exchange in self.available_exchanges:
            status = "(current)" if exchange == self.config['exchange'] else ""
            print(f"{Fore.GREEN}{exchange} {Fore.YELLOW}{status}")
    
    def do_list_strategies(self, arg):
        """List available trading strategies."""
        print(f"{Fore.CYAN}Available strategies:")
        for strategy in self.available_strategies:
            status = "(current)" if strategy == self.config['strategy'] else ""
            print(f"{Fore.GREEN}{strategy} {Fore.YELLOW}{status}")
    
    def do_show_config(self, arg):
        """Show current configuration."""
        print(f"{Fore.CYAN}Current configuration:")
        for key, value in self.config.items():
            print(f"{Fore.GREEN}{key}: {Fore.WHITE}{value}")
    
    def do_set_parameter(self, arg):
        """Set configuration parameter."""
        args = arg.split()
        if len(args) < 2:
            print(f"{Fore.RED}Error: Missing parameter name or value")
            print("Usage: set_parameter <name> <value>")
            return
        
        param_name = args[0].lower()
        param_value = args[1]
        
        # Handle special cases for validation
        if param_name == 'exchange':
            if param_value not in self.available_exchanges:
                print(f"{Fore.RED}Error: Unknown exchange: {param_value}")
                print("Use 'list_exchanges' to see available options.")
                return
        elif param_name == 'strategy':
            if param_value not in self.available_strategies:
                print(f"{Fore.RED}Error: Unknown strategy: {param_value}")
                print("Use 'list_strategies' to see available options.")
                return
        elif param_name == 'cash_at_risk':
            try:
                param_value = float(param_value)
                if param_value <= 0 or param_value > 1:
                    print(f"{Fore.RED}Error: cash_at_risk must be between 0 and 1")
                    return
            except ValueError:
                print(f"{Fore.RED}Error: cash_at_risk must be a float value")
                return
        elif param_name in ['start_date', 'end_date']:
            try:
                # Validate date format
                datetime.datetime.strptime(param_value, '%Y-%m-%d')
            except ValueError:
                print(f"{Fore.RED}Error: Invalid date format. Use YYYY-MM-DD")
                return
        
        # Update config if validation passed
        if param_name in self.config:
            self.config[param_name] = param_value
            print(f"{Fore.GREEN}Parameter {param_name} set to {param_value}")
        else:
            print(f"{Fore.RED}Error: Unknown parameter: {param_name}")
            print("Available parameters: " + ", ".join(self.config.keys()))
    
    def do_save_config(self, arg):
        """Save configuration to file."""
        if not arg:
            filename = 'crypto_config.json'
        else:
            filename = arg
            if not filename.endswith('.json'):
                filename += '.json'
        
        try:
            with open(os.path.join('crypto_journey', filename), 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"{Fore.GREEN}Configuration saved to {filename}")
        except Exception as e:
            print(f"{Fore.RED}Error saving configuration: {e}")
    
    def do_load_config(self, arg):
        """Load configuration from file."""
        if not arg:
            filename = 'crypto_config.json'
        else:
            filename = arg
            if not filename.endswith('.json'):
                filename += '.json'
        
        try:
            with open(os.path.join('crypto_journey', filename), 'r') as f:
                self.config = json.load(f)
            print(f"{Fore.GREEN}Configuration loaded from {filename}")
        except FileNotFoundError:
            print(f"{Fore.RED}Error: File not found: {filename}")
        except json.JSONDecodeError:
            print(f"{Fore.RED}Error: Invalid JSON format in {filename}")
        except Exception as e:
            print(f"{Fore.RED}Error loading configuration: {e}")
    
    def do_run_backtest(self, arg):
        """Run backtest with current configuration."""
        try:
            print(f"{Fore.CYAN}Initializing backtest with configuration:")
            self.do_show_config("")
            
            print(f"\n{Fore.YELLOW}Starting backtest... This may take a moment.")
            
            # Parse dates
            start_date = datetime.datetime.strptime(self.config['start_date'], '%Y-%m-%d')
            end_date = datetime.datetime.strptime(self.config['end_date'], '%Y-%m-%d')
            
            # Set up backtest parameters
            exchange_id = self.config['exchange']
            coin = self.config['coin']
            quote = self.config['quote']
            
            print(f"Running backtest for {coin}/{quote} on {exchange_id} from {start_date} to {end_date}")
            
            # This is a placeholder for actual backtest execution
            # In a future update, we'll import and run actual strategies
            print(f"\n{Fore.RED}Note: This is a placeholder for the backtest functionality.")
            print(f"{Fore.RED}In the future, this will run the actual {self.config['strategy']} strategy.")
            
        except Exception as e:
            print(f"{Fore.RED}Error running backtest: {e}")
    
    # Override methods
    def emptyline(self):
        """Do nothing on empty line."""
        pass
    
    def default(self, line):
        """Handle unknown command."""
        print(f"{Fore.RED}Unknown command: {line}")
        print(f"Type 'help' to see available commands.")

def main():
    try:
        CryptoShell().cmdloop()
    except KeyboardInterrupt:
        print("\nExiting due to keyboard interrupt")
    except Exception as e:
        print(f"{Fore.RED}Error: {e}")
        
if __name__ == '__main__':
    main()
