from GamePlay import GEScenario
from .Utils.GEPlayerTracker import GEPlayerTracker
from .Utils import GetPlayers
from random import shuffle
import re
import GEPlayer, GEUtil, GEMPGameRules, GEGlobal

USING_API = GEGlobal.API_VERSION_1_2_0

# Created by Euphonic for GoldenEye: Source 5.0
# For more information, visit https://euphonic.dev/goldeneye-source/

#    * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / *
TrueColorsVersion = "^uTrueColors ^11.0.0"
#    * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / * / *

class TrueColors(GEScenario):
    # Track player-related variables
    PLAYER_COLOR = "Stores player color"

    def __init__( self ):
        super(TrueColors, self).__init__()

        self.playerTracker = GEPlayerTracker( self )

        self.topPlayers = []
        
        self.colors = []

        self.colorsOne = [
            GEUtil.CColor(255,51,0,255), #Red
            GEUtil.CColor(255,204,153,255), #Peach
            GEUtil.CColor(255,255,0,255), #Yellow
            GEUtil.CColor(0,255,0,255), #Lime
            GEUtil.CColor(153,204,255,255), #Sky
            GEUtil.CColor(191,0,255,255), #Purple
            GEUtil.CColor(255,153,255,255), #Pink
            GEUtil.CColor(255,255,255,255) #White
        ]

        self.colorsTwo = [
            GEUtil.CColor(255,153,153,255), #Tangerine
            GEUtil.CColor(204,102,0,255), #Brown
            GEUtil.CColor(255,191,0,255), #Gold
            GEUtil.CColor(204,255,102,255), #Mint
            GEUtil.CColor(0,0,255,255), #Cyan
            GEUtil.CColor(17,136,255,255), #Blue
            GEUtil.CColor(255,0,255,255), #Magenta
            GEUtil.CColor(119,119,119,255), #Gray
        ]

        self.colorDefault = GEUtil.Color( 15, 143, 11, 255 )
        self.colorMI6 = GEUtil.Color( 94, 171, 231, 255 )
        self.colorJanus = GEUtil.Color( 206, 43, 43, 255 )

        self.iconShapeDefault = ""
        self.iconShapeTopPlayer = "sprites/hud/radar/star"
        self.iconShapeMI6 = "sprites/hud/radar/capture_point"
        self.iconShapeJanus = "sprites/hud/radar/xsm"
        
        self.indicatorSymbolDefault = "(                 )"
        self.indicatorSymbolStar = "*                 *"
        self.indicatorSymbolMI6 = "O                 O"
        self.indicatorSymbolJanus = "X                 X"
        
        self.changeColorErrorText = "^dNo colors available"
        
        self.killerMessageText = "^| killed you"
        self.colorMessageXPos = -1
        self.colorMessageYPos = 0.6
        self.colorMessageChannel = 1
        self.colorMessageTime = 3
        
        self.indicatorXPos = -1
        self.indicatorYPos = 0.85
        self.indicatorYPosStar = 0.86
        self.indicatorChannel = 0

    def GetPrintName( self ):
        return "True Colors"
        
    def GetScenarioHelp( self, help_obj ):
        help_obj.SetDescription( "Each player gets their own unique radar color.\n\nIn free for all, the top-scoring players are marked by stars. In teamplay, Janus players are Xs and MI6 players are Os.\n\nTeamplay: Toggleable\n\nCreated by Euphonic" )
        help_obj.SetInfo("A more colorful way to play", "https://euphonic.dev/goldeneye-source/true-colors")
        
        pane = help_obj.AddPane( "truecolors1" )
        help_obj.AddHelp( pane, "tc_info", "Each player gets their own radar icon color" )
        help_obj.AddHelp( pane, "", "Your icon's color and shape are displayed next to your radar")
        help_obj.AddHelp( pane, "", "In teamplay, Janus players are Xs and MI6 players are Os")
        
        help_obj.SetDefaultPane( pane )
        
    def GetGameDescription( self ):
        if GEMPGameRules.IsTeamplay():
            return "Team True Colors"
        else:
            return "True Colors"
        
    def GetTeamPlay( self ):
        return GEGlobal.TEAMPLAY_TOGGLE

    def OnPlayerSay( self, player, text ):
        if text == "!version":
            GEUtil.ClientPrint(None, GEGlobal.HUD_PRINTTALK, TrueColorsVersion)
        if text == "!color":
            self.showColorMessage(player, player)    
        if text == "!changecolor":
            playerRadarColor = self.playerTracker.GetValue( player, self.PLAYER_COLOR )
            if playerRadarColor and len(self.colors):
                self.colors = [ playerRadarColor ] + self.colors
                self.playerTracker.SetValue( player, self.PLAYER_COLOR, self.colors.pop() )
                if player.IsInRound():
                    self.showColorIndicator( player )
                self.showColorMessage(player, player)
            else:
                GEUtil.ClientPrint(player, GEGlobal.HUD_PRINTTALK, self.changeColorErrorText)
                return True
        
    def OnLoadGamePlay( self ):
        self.CreateCVar("tc_topstar", "0", "When enabled, the top-scoring players in free-for-all mode have star icons. Requires players have downloaded the custom star icons.")
        GEMPGameRules.GetRadar().SetForceRadar( True )
        shuffle(self.colorsTwo); shuffle(self.colorsOne)
        self.colors = self.colorsTwo + self.colorsOne
    
    def OnUnloadGamePlay( self ):
        self.hideColorIndicator( None )

    def OnCVarChanged( self, name, oldvalue, newvalue ):
        if name == "tc_topstar" and not GEMPGameRules.IsTeamplay():
            self.updateTopPlayers()

    def OnRoundBegin( self ):
        self.topPlayers = []
        GEMPGameRules.ResetAllPlayersScores()

    def OnRoundEnd( self ):
        self.hideColorIndicator( None )

    def OnPlayerConnect( self, player ):
        self.playerTracker.SetValue( player, self.PLAYER_COLOR, False )

        if len(self.colors):
            self.playerTracker.SetValue( player, self.PLAYER_COLOR, self.colors.pop() )

    def CanPlayerChangeTeam( self, player, oldteam, newteam, wasforced ):
        if player in self.topPlayers and not GEMPGameRules.IsTeamplay():
            self.updateTopPlayers()
        return True

    def OnPlayerDisconnect( self, player ):
        playerRadarColor = self.playerTracker.GetValue( player, self.PLAYER_COLOR )
        if playerRadarColor:
            self.colors = [ playerRadarColor ] + self.colors
        
        if player in self.topPlayers and not GEMPGameRules.IsTeamplay():
            self.updateTopPlayers()

    def OnPlayerSpawn( self, player ):
        # Fix issue with bots not being assigned colors before first spawn
        if player.GetSteamID() == "__BOT__" and player.IsInitialSpawn():
            player.ForceRespawn()
        
        self.setPlayerRadarContact( player )
        self.showColorIndicator( player )
            
    def OnPlayerKilled( self, victim, killer, weapon ):
        GEScenario.OnPlayerKilled( self, victim, killer, weapon )
        
        if not GEMPGameRules.IsTeamplay():
            self.updateTopPlayers()

        self.hideColorIndicator( victim )
        if victim and killer and killer != victim:
            self.showColorMessage( victim, killer )

    def updateTopPlayers( self ):        
        newTopPlayers = []
        if int(GEUtil.GetCVarValue("tc_topstar")):
            for player in GetPlayers():
                playerScore = GEPlayer.CGEMPPlayer.GetRoundScore( player )
                if playerScore > 0:
                    if not newTopPlayers:
                        newTopPlayers = [player]
                    else:
                        oldScore = GEPlayer.CGEMPPlayer.GetRoundScore( newTopPlayers[0] )
                        if playerScore > oldScore:
                            newTopPlayers = [player]
                        elif playerScore == oldScore:
                            newTopPlayers.append( player )

        oldTopPlayers = self.topPlayers
        self.topPlayers = newTopPlayers
                    
        for player in ( set(newTopPlayers) ^ set(oldTopPlayers) ):
            if not player.IsDead():
                self.setPlayerRadarContact( player )
                self.showColorIndicator( player )

    def getIconShape( self, player ):
        if player.GetTeamNumber() == GEGlobal.TEAM_MI6:
            return self.iconShapeMI6
        elif player.GetTeamNumber() == GEGlobal.TEAM_JANUS:
            return self.iconShapeJanus
        elif player in self.topPlayers:
            return self.iconShapeTopPlayer
        else:
            return self.iconShapeDefault
    
    def getIndicatorShape( self, player ):
        if player.GetTeamNumber() == GEGlobal.TEAM_MI6:
            return self.indicatorSymbolMI6
        elif player.GetTeamNumber() == GEGlobal.TEAM_JANUS:
            return self.indicatorSymbolJanus
        elif player in self.topPlayers:
            return self.indicatorSymbolStar
        else:
            return self.indicatorSymbolDefault

    def getDefaultColor( self, player ):
        if player.GetTeamNumber() == GEGlobal.TEAM_MI6:
            return self.colorMI6
        elif player.GetTeamNumber() == GEGlobal.TEAM_JANUS:
            return self.colorJanus
        else:
            return self.colorDefault
    
    def setPlayerRadarContact( self, player ):
        if player:
            playerRadarColor = self.playerTracker.GetValue( player, self.PLAYER_COLOR )
            if not playerRadarColor:
                if len(self.colors):
                    playerRadarColor = self.colors.pop()
                    self.playerTracker.SetValue( player, self.PLAYER_COLOR, playerRadarColor )
                else:
                    playerRadarColor = self.getDefaultColor(player)
    
            GEMPGameRules.GetRadar().AddRadarContact( player, GEGlobal.RADAR_TYPE_PLAYER, False, self.getIconShape( player ), playerRadarColor)
    
    def showColorMessage( self, player, killer ):
        messageText = self.cleanPlayerName( killer.GetCleanPlayerName() )
        GEUtil.Msg(messageText)
        if player != killer:
            messageText = messageText + self.killerMessageText
        messageColor = self.playerTracker.GetValue( killer, self.PLAYER_COLOR )
        if not messageColor:
            messageColor = self.getDefaultColor(player)
        GEUtil.HudMessage( player, messageText , self.colorMessageXPos, self.colorMessageYPos, messageColor, self.colorMessageTime, self.colorMessageChannel )
    
    def showColorIndicator( self, player ):
        playerRadarColor = self.playerTracker.GetValue( player, self.PLAYER_COLOR )
        if not playerRadarColor:
            playerRadarColor = self.getDefaultColor(player)
                
        indicatorText = self.getIndicatorShape(player)
        
        if indicatorText == self.indicatorSymbolStar:
            playerIndicatorYPos = self.indicatorYPosStar
        else:
            playerIndicatorYPos = self.indicatorYPos

        GEUtil.HudMessage( player, indicatorText , self.indicatorXPos, playerIndicatorYPos, playerRadarColor, float('inf'), self.indicatorChannel )
        
    def hideColorIndicator( self, player ):
        GEUtil.HudMessage( player, "" , -1, -1, GEUtil.CColor(255,255,255,255), float('inf'), self.indicatorChannel )
        
    def cleanPlayerName( self, name ):
        # This custom function serves the same purpose as GetCleanPlayerName(), which is currently broken
        newname = False
        while name != newname:
            newname = name
            name = re.sub(r'\^[a-z0-9]', '', name)
        return name