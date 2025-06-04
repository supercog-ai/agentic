import json
from typing import Any, Generator, List
from pydantic import BaseModel, Field
from datetime import datetime

from agentic.common import Agent, AgentRunner
from agentic.agentic_secrets import agentic_secrets
from agentic.events import Event, Prompt, TurnEnd, ChatOutput, PromptStarted
from agentic.models import GPT_4O, CLAUDE
from agentic.tools import TavilySearchTool

ANALYZER_MODEL = GPT_4O
PREDICTOR_MODEL = CLAUDE

TEAM_LISTER_INSTRUCTIONS = """
You are a specialist in extracting and organizing NCAA basketball tournament data.
            
Your task is to analyze web search results and extract:
1. All team names in the NCAA tournament
2. Their seeds (numbers 1-16)
4. When available, their win-loss records and conferences

Look for patterns like:
- "1. Kansas (East Region)"
- "Kansas Jayhawks (1 seed, East)"
- "East Region: 1. Kansas (29-3)"

Be thorough and consistent in your extraction. Handle variations in team naming (e.g., "UNC" vs "North Carolina").

Return the data in a structured format with each team's name, seed, and region.
"""

TEAM_RESEARCHER_INSTRUCTIONS = """
You are a college basketball research specialist. Your task is to research comprehensive statistics and information about NCAA basketball teams for tournament prediction purposes.

For each team you are assigned:
1. Find the team's current season statistics (overall record, conference record, seed)
2. Research key offensive metrics (points per game, field goal %, 3-point %, offensive efficiency)
3. Research key defensive metrics (points allowed, defensive efficiency, steals, blocks)
4. Identify the team's star players and their statistics
5. Research the team's recent performance (last 10 games)
6. Find information about the team's tournament history in recent years
7. Identify notable wins and losses during the season
8. Research the team's performance against quality opponents
9. Analyze the team's coaching staff and style of play
10. Identify clear strengths and weaknesses

Be thorough in your research, as this information will be critical for making accurate predictions in matchup analyses. Focus on the most recent and relevant statistics that would affect tournament performance.

Return the information in the required TeamStats format, with concise but comprehensive data in each field.
"""

MATCHUP_ANALYZER_INSTRUCTIONS="""
You are a college basketball matchup analyst specializing in tournament predictions. Your task is to analyze matchups between two NCAA basketball teams and predict the winner based on comprehensive analysis.

For each matchup you are given:
1. Review both teams' detailed statistics (provided in the TeamStats format)
2. Consider the following factors in your analysis:
   - Seeding and overall record
   - Offensive and defensive efficiency
   - Star player matchups and potential advantages
   - Coaching experience in tournament settings
   - Recent performance and momentum
   - Conference strength and quality of wins
   - Head-to-head matchups if applicable
   - Style of play compatibility/clashes
   - Tournament experience
   - Any injury information available

3. Compare the teams across all dimensions to identify advantages
4. Consider historical tournament trends (e.g., frequency of upsets at each seed matchup)
5. Assess the likelihood of an upset based on the specific team matchup
6. Determine a confidence level (1-10) for your prediction
7. Provide detailed reasoning for your prediction

Be objective in your analysis. While basketball tournaments are unpredictable and upsets happen, your goal is to make the most probable prediction based on available data. Consider both quantitative statistics and qualitative factors.

Return your prediction in the required Matchup format, with a particularly detailed reasoning section that explains your decision process.
"""

BRACKET_BUILDER_INSTRUCTIONS="""
You are a tournament bracket building specialist. Your task is to take individual matchup predictions and assemble them into a complete, coherent NCAA tournament bracket.
ONLY USE THE MATCHUP PREDICTIONS YOU ARE GIVEN. DO NOT MAKE UP MATCHUPS.

Given a full set of matchup predictions:
1. Organize all predictions by region and round
2. Ensure bracket integrity by confirming matchup winners advance properly to subsequent rounds
3. Create a visually clear representation of the bracket showing:
   - All teams by seed and name
   - All predicted winners clearly marked
   - The advancing path through each region
   - Final Four matchups
   - Championship matchup and overall winner

4. Include a summary of notable predictions:
   - Major upsets (teams beating opponents seeded at least 4 spots higher)
   - Cinderella stories (teams seeded 10+ reaching Sweet 16 or beyond)
   - Top seeds that fail to reach expected rounds
   
5. Provide brief rationales for Final Four and Championship picks

The bracket should be formatted in a way that's easy to read in text format, using clear spacing, dividers, and region labels. Number each matchup for easy reference.

Your goal is to present a professional, comprehensive bracket that could be used by serious basketball fans for tournament prediction purposes.
"""

class TeamBase(BaseModel):
    name: str = Field(description="Full name of the basketball team")
    seed: int = Field(description="Tournament seed (1-16)")
    region: str = Field(description="Region the team is in (East, West, Midwest, South)")

class TeamList(BaseModel):
    teams: List[TeamBase]

class TeamStats(TeamBase):
    record: str = Field(description="Win-loss record (e.g., '25-7')")
    conference: str = Field(description="Conference the team belongs to")
    key_players: List[str] = Field(description="List of key players and their stats")
    offensive_stats: str = Field(description="Key offensive statistics and rankings")
    defensive_stats: str = Field(description="Key defensive statistics and rankings")
    tournament_history: str = Field(description="Recent tournament performance")
    notable_wins_losses: str = Field(description="Notable wins and losses this season")
    strengths: List[str] = Field(description="Team's key strengths")
    weaknesses: List[str] = Field(description="Team's key weaknesses")
    
class Matchup(BaseModel):
    team1: str = Field(description="First team in the matchup")
    team2: str = Field(description="Second team in the matchup")
    region: str = Field(description="Tournament region")
    round: str = Field(description="Tournament round (First Round, Second Round, etc.)")
    predicted_winner: str = Field(description="Predicted winner of this matchup")
    confidence: int = Field(description="Confidence in prediction (1-10)")
    reasoning: str = Field(description="Detailed reasoning for the prediction")

class Tournament(BaseModel):
    year: int = Field(description="Tournament year")
    regions: List[str] = Field(description="List of tournament regions")
    teams: List[TeamStats] = Field(description="List of all teams in tournament")
    matchups: List[Matchup] = Field(description="List of all matchup predictions")

TEAMS_LIST = TeamList(teams=[
    # East Region
    TeamBase(name="Duke Blue Devils", seed=1, region="East"),
    TeamBase(name="Alabama Crimson Tide", seed=2, region="East"),
    TeamBase(name="Wisconsin Badgers", seed=3, region="East"),
    TeamBase(name="Arizona Wildcats", seed=4, region="East"),
    TeamBase(name="Oregon Ducks", seed=5, region="East"),
    TeamBase(name="BYU Cougars", seed=6, region="East"),
    TeamBase(name="St. Mary's Gaels", seed=7, region="East"),
    TeamBase(name="Mississippi State Bulldogs", seed=8, region="East"),
    TeamBase(name="Baylor Bears", seed=9, region="East"),
    TeamBase(name="Vanderbilt Commodores", seed=10, region="East"),
    TeamBase(name="VCU Rams", seed=11, region="East"),
    TeamBase(name="Liberty Flames", seed=12, region="East"),
    TeamBase(name="Akron Zips", seed=13, region="East"),
    TeamBase(name="Montana Grizzlies", seed=14, region="East"),
    TeamBase(name="Robert Morris Colonials", seed=15, region="East"),
    TeamBase(name="Mount St. Mary's Mountaineers", seed=16, region="East"),

    # Midwest Region
    TeamBase(name="Houston Cougars", seed=1, region="Midwest"),
    TeamBase(name="Tennessee Volunteers", seed=2, region="Midwest"),
    TeamBase(name="Kentucky Wildcats", seed=3, region="Midwest"),
    TeamBase(name="Purdue Boilermakers", seed=4, region="Midwest"),
    TeamBase(name="Clemson Tigers", seed=5, region="Midwest"),
    TeamBase(name="Illinois Fighting Illini", seed=6, region="Midwest"),
    TeamBase(name="UCLA Bruins", seed=7, region="Midwest"),
    TeamBase(name="Gonzaga Bulldogs", seed=8, region="Midwest"),
    TeamBase(name="Georgia Bulldogs", seed=9, region="Midwest"),
    TeamBase(name="Utah State Aggies", seed=10, region="Midwest"),
    TeamBase(name="Xavier Musketeers", seed=11, region="Midwest"),
    TeamBase(name="McNeese Cowboys", seed=12, region="Midwest"),
    TeamBase(name="High Point Panthers", seed=13, region="Midwest"),
    TeamBase(name="Troy Trojans", seed=14, region="Midwest"),
    TeamBase(name="Wofford Terriers", seed=15, region="Midwest"),
    TeamBase(name="SIU Edwardsville Cougars", seed=16, region="Midwest"),

    # South Region
    TeamBase(name="Auburn Tigers", seed=1, region="South"),
    TeamBase(name="Michigan State Spartans", seed=2, region="South"),
    TeamBase(name="Iowa State Cyclones", seed=3, region="South"),
    TeamBase(name="Texas A&M Aggies", seed=4, region="South"),
    TeamBase(name="Michigan Wolverines", seed=5, region="South"),
    TeamBase(name="Ole Miss Rebels", seed=6, region="South"),
    TeamBase(name="Marquette Golden Eagles", seed=7, region="South"),
    TeamBase(name="Louisville Cardinals", seed=8, region="South"),
    TeamBase(name="Creighton Bluejays", seed=9, region="South"),
    TeamBase(name="New Mexico Lobos", seed=10, region="South"),
    TeamBase(name="North Carolina Tar Heels", seed=11, region="South"),
    TeamBase(name="UC San Diego Tritons", seed=12, region="South"),
    TeamBase(name="Yale Bulldogs", seed=13, region="South"),
    TeamBase(name="Lipscomb Bisons", seed=14, region="South"),
    TeamBase(name="Bryant Bulldogs", seed=15, region="South"),
    TeamBase(name="Alabama State Hornets", seed=16, region="South"),

    # West Region
    TeamBase(name="Florida Gators", seed=1, region="West"),
    TeamBase(name="St. John's Red Storm", seed=2, region="West"),
    TeamBase(name="Texas Tech Red Raiders", seed=3, region="West"),
    TeamBase(name="Maryland Terrapins", seed=4, region="West"),
    TeamBase(name="Memphis Tigers", seed=5, region="West"),
    TeamBase(name="Missouri Tigers", seed=6, region="West"),
    TeamBase(name="Kansas Jayhawks", seed=7, region="West"),
    TeamBase(name="UConn Huskies", seed=8, region="West"),
    TeamBase(name="Oklahoma Sooners", seed=9, region="West"),
    TeamBase(name="Arkansas Razorbacks", seed=10, region="West"),
    TeamBase(name="Drake Bulldogs", seed=11, region="West"),
    TeamBase(name="Colorado State Rams", seed=12, region="West"),
    TeamBase(name="Grand Canyon Antelopes", seed=13, region="West"),
    TeamBase(name="UNC Wilmington Seahawks", seed=14, region="West"),
    TeamBase(name="Omaha Mavericks", seed=15, region="West"),
    TeamBase(name="Norfolk State Spartans", seed=16, region="West")
])

class MarchMadnessAgent(Agent):
    tournament: Tournament | None = None
    
    def __init__(
        self,
        name: str="March Madness Predictor",
        welcome="I am the March Madness Prediction agent. I'll analyze matchups and build a complete tournament bracket prediction.",
        model: str=ANALYZER_MODEL,
        verbose: bool = False,
        **kwargs
    ):
        super().__init__(
            name, 
            welcome=welcome,
            model=model,
            **kwargs
        )
        self.tavily_tool = TavilySearchTool(api_key=agentic_secrets.get_required_secret("TAVILY_API_KEY"))
        self.verbose = verbose

        self.team_lister = Agent(
            name="Team Lister",
            instructions=TEAM_LISTER_INSTRUCTIONS,
            model=ANALYZER_MODEL,
            result_model=TeamList,
            tools=[self.tavily_tool],
        )
        
        # Team Researcher gathers detailed stats about each team
        self.team_researcher = Agent(
            name="Team Researcher",
            instructions=TEAM_RESEARCHER_INSTRUCTIONS,
            model=ANALYZER_MODEL,
            result_model=TeamStats,
            memories=[f"The current date is {datetime.now().strftime('%Y-%m-%d')}"]
        )
        
        # Matchup Analyzer compares teams and predicts winners
        self.matchup_analyzer = Agent(
            name="Matchup Analyzer",
            instructions=MATCHUP_ANALYZER_INSTRUCTIONS,
            model=PREDICTOR_MODEL,
            result_model=Matchup
        )
        
        # Bracket Builder takes all matchup predictions and creates the full bracket
        self.bracket_builder = Agent(
            name="Bracket Builder",
            instructions=BRACKET_BUILDER_INSTRUCTIONS,
            model=ANALYZER_MODEL
        )

    def next_turn(
        self,
        request: str|Prompt,
        request_context: dict = {},
        request_id: str = None,
        continue_result: dict = {},
        debug = "",
    ) -> Generator[Event, Any, Any]:
        """Main workflow orchestration for tournament prediction"""

        agent_instance = self._get_agent_for_request(request_id)
        if not self.thread_id and self.db_path:
            self.init_run_tracking(agent_instance)
        
        tournament_year = request_context.get("year", datetime.now().year)
        
        # Yield the initial prompt
        yield PromptStarted(self.name, {"content": request.payload})
        
        # Initialize tournament structure
        self.tournament = Tournament(
            year=tournament_year,
            regions=["EAST", "WEST", "SOUTH", "MIDWEST"],
            teams=[],
            matchups=[]
        )
        
        # 1. Get initial tournament team list
        #teams_list: TeamList = yield from self.team_lister.final_result(f"Research march madness teams, seeds, and regions for {tournament_year}")
        teams_list = TEAMS_LIST
        self.region_seeds = self.get_region_seeds(teams_list.teams)

        if self.verbose:
            yield ChatOutput(self.name, {"content": f"Retrieved {len(teams_list.teams)} teams for the {tournament_year} NCAA Tournament"})
        
        # 2. Research each team in depth
        for team in teams_list.teams:
            team_stats = yield from self.team_researcher.final_result(
                f"Research detailed statistics for {team.name} basketball team",
                request_context={"name": team.name, "year": tournament_year}
            )
            self.tournament.teams.append(team_stats)
            if self.verbose:
                yield ChatOutput(self.team_researcher.name, {"content": f"Completed research on {team.name}"})
        
        
        # 3. Generate first round matchups
        first_round_matchups = self.generate_first_round_matchups()
        
        # 4. Analyze each matchup and predict winners
        bracket_rounds = ["First Round", "Second Round", "Sweet 16", "Elite Eight", "Final Four", "Championship"]
        current_matchups = first_round_matchups
        
        for round_name in bracket_rounds:
            if self.verbose:
                yield ChatOutput(self.name, {"content": f"Analyzing {round_name} matchups..."})
            next_round_matchups: list[Matchup] = []
            
            for matchup in current_matchups:
                # Analyze matchup and predict winner
                prediction: Matchup = yield from self.matchup_analyzer.final_result(
                    f"Analyze the {round_name} matchup between {matchup['team1']} and {matchup['team2']}",
                    request_context={
                        "team1": self.get_team_stats(matchup["team1"]),
                        "team2": self.get_team_stats(matchup["team2"]),
                        "round": round_name,
                        "region": matchup["region"]
                    }
                )
                self.tournament.matchups.append(prediction)
                
                # Create next round matchup if not final
                if round_name != "Championship":
                    if round_name == "Elite Eight":
                        # Handle Final Four matchups specifically
                        self.handle_final_four_advancement(next_round_matchups, prediction)
                    else:
                        # Handle standard round advancement
                        self.handle_standard_advancement(next_round_matchups, prediction)
                            

                    current_matchups = next_round_matchups
        
        # 5. Build the complete bracket
        formatted_tournament_data = self.format_tournament_data()

        final_bracket = yield from self.bracket_builder.final_result(
            f"Build a complete NCAA Tournament bracket based on these matchup predictions:\n\n{formatted_tournament_data}",
            request_context={
                "formatted_data": formatted_tournament_data,
                "matchups": json.dumps([m.model_dump() for m in self.tournament.matchups], default=str),
                "teams": json.dumps([t.model_dump() for t in self.tournament.teams], default=str)
            }
        )
        
        yield ChatOutput(
            self.name, 
            {"content": final_bracket}
        )
        
        yield TurnEnd(
            self.name,
            [{"role": "assistant", "content": final_bracket}],
            thread_context=None,
        )

    def generate_first_round_matchups(self):
        """Generate the first round of matchups based on seeding"""
        first_round = []
        
        # Standard NCAA tournament first round matchups by seed
        seed_matchups = [(1, 16), (8, 9), (5, 12), (4, 13), (6, 11), (3, 14), (7, 10), (2, 15)]
        
        # Create matchups for each region
        for region in self.tournament.regions:
            for seed1, seed2 in seed_matchups:
                team1 = self.region_seeds.get(region, {}).get(seed1, f"{seed1}-Seed ({region})")
                team2 = self.region_seeds.get(region, {}).get(seed2, f"{seed2}-Seed ({region})")
                
                matchup = {
                    "team1": team1,
                    "team2": team2,
                    "region": region,
                    "seeds": (seed1, seed2)  # Store seeds for easier bracket construction
                }
                
                first_round.append(matchup)
        
        # If we're using the standard 4-region tournament, we should have 32 matchups (64 teams)
        if len(first_round) != 32 and self.verbose:
            print(f"Warning: Generated {len(first_round)} first-round matchups instead of the expected 32.")
        
        return first_round
    
    def handle_final_four_advancement(self, next_round_matchups: list[Matchup], prediction: Matchup):
        """Handle advancement to Final Four, pairing East/Midwest and South/West regions"""
        east_midwest = ["EAST", "MIDWEST"]
        south_west = ["SOUTH", "WEST"]
        current_region = prediction.region
        
        # Find appropriate matchup to add this team to
        for matchup in next_round_matchups:
            # If we already have a matchup started with the appropriate region grouping
            if (current_region in east_midwest and matchup["region"] in east_midwest) or \
            (current_region in south_west and matchup["region"] in south_west):
                if matchup["team2"] == "TBD":
                    matchup["team2"] = prediction.predicted_winner
                    matchup["region"] = "Final Four"
                    return
        
        # No appropriate matchup found, create a new one
        next_round_matchups.append({
            "team1": prediction.predicted_winner,
            "team2": "TBD",
            "region": prediction.region
        })


    def handle_standard_advancement(self, next_round_matchups: list[Matchup], prediction: Matchup):
        """Handle standard advancement for earlier rounds"""
        # Check if we have an open matchup (with "TBD" as team2)
        for matchup in next_round_matchups:
            if matchup["team2"] == "TBD" and matchup["region"] == prediction.region:
                matchup["team2"] = prediction.predicted_winner
                return
        
        # No open matchup found for this region, create a new one
        next_round_matchups.append({
            "team1": prediction.predicted_winner,
            "team2": "TBD",
            "region": prediction.region
        })
    
    def get_team_stats(self, name):
        """Retrieve stats for a specific team from the tournament data"""
        for team in self.tournament.teams:
            if team.name == name:
                return team
        return None
    
    def get_region_seeds(self, teams: List[TeamBase]):
        """Get the seed for each team in the tournament"""
        region_seeds = {}
        for team in teams:
            region = team.region.upper()
            seed = team.seed
            if region not in region_seeds:
                region_seeds[region] = {}
            region_seeds[region][seed] = team.name
        return region_seeds
    
    def format_tournament_data(self):
        """Format tournament data for the bracket builder in a clear, structured way"""
        
        # Create a seed lookup for all teams
        seed_lookup = {}
        for team in self.tournament.teams:
            seed_lookup[team.name] = team.seed
        
        # Organize matchups by round and region
        organized_matchups = {}
        round_order = {
            "First Round": 1,
            "Second Round": 2,
            "Sweet 16": 3,
            "Elite Eight": 4,
            "Final Four": 5,
            "Championship": 6
        }
        
        for matchup in self.tournament.matchups:
            round_name = matchup.round
            region = matchup.region
            
            if round_name not in organized_matchups:
                organized_matchups[round_name] = {}
            
            if region not in organized_matchups[round_name]:
                organized_matchups[round_name][region] = []
            
            # Add seed info to team names
            team1_seed = seed_lookup.get(matchup.team1, "?")
            team2_seed = seed_lookup.get(matchup.team2, "?")
            
            formatted_matchup = {
                "team1": f"({team1_seed}) {matchup.team1}",
                "team2": f"({team2_seed}) {matchup.team2}",
                "winner": f"({seed_lookup.get(matchup.predicted_winner, '?')}) {matchup.predicted_winner}",
                "confidence": matchup.confidence,
                "reasoning": matchup.reasoning
            }
            
            organized_matchups[round_name][region].append(formatted_matchup)
        
        # Sort rounds in proper order
        sorted_rounds = sorted(organized_matchups.keys(), key=lambda r: round_order.get(r, 99))
        
        # Format as text
        formatted_text = []
        formatted_text.append(f"# NCAA TOURNAMENT {self.tournament.year} BRACKET PREDICTION\n")
        
        for round_name in sorted_rounds:
            formatted_text.append(f"\n## {round_name.upper()}\n")
            
            for region in self.tournament.regions:
                if region in organized_matchups[round_name]:
                    formatted_text.append(f"\n### {region} REGION\n")
                    
                    for i, matchup in enumerate(organized_matchups[round_name][region], 1):
                        formatted_text.append(
                            f"{i}. {matchup['team1']} vs {matchup['team2']}\n"
                            f"   Winner: {matchup['winner']} (Confidence: {matchup['confidence']}/10)\n"
                        )
        
        # Add special sections for Final Four and Championship if they exist
        if "Final Four" in organized_matchups:
            formatted_text.append("\n## FINAL FOUR\n")
            for region, matchups in organized_matchups["Final Four"].items():
                for matchup in matchups:
                    formatted_text.append(
                        f"{matchup['team1']} vs {matchup['team2']}\n"
                        f"Winner: {matchup['winner']} (Confidence: {matchup['confidence']}/10)\n"
                    )
        
        if "Championship" in organized_matchups:
            formatted_text.append("\n## CHAMPIONSHIP\n")
            for region, matchups in organized_matchups["Championship"].items():
                for matchup in matchups:
                    formatted_text.append(
                        f"{matchup['team1']} vs {matchup['team2']}\n"
                        f"CHAMPION: {matchup['winner']} (Confidence: {matchup['confidence']}/10)\n"
                    )
        
        return "\n".join(formatted_text)


march_madness_predictor = MarchMadnessAgent()

if __name__ == "__main__":
    AgentRunner(march_madness_predictor).repl_loop()