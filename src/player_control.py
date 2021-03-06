# player_control.py 05Nov2018
"""
Player control window layout
Omitted to save room:
    steven (stay even) to right of level

players
Name      Label    Playing  Color    col bg  Voice Help   Pause Auto level
    
--------- ------   -        -------  ------  ----  -----  ----- ---- -----
comp1     c1       ()       gray     white   ( )   ( )    .1    x    0
comp2     c2       ()       gray     white   ( )   ( )    .1    x    -1
Alex      Ax       (.)      pink     white   (.)   ( )
Decklan   D        ()       blue     white   (.)   ( )
Avery     Av       ()       pink     white   (.)   ( )
Grampy    Gp       (.)      blue     white   (.)   ( )
Grammy    Gm       (.)      pink     white   (.)   ( )

[Add] [Change] [Remove]
"""
###from memory_profiler import profile


from tkinter import *
import random
from select_error import SelectError
from select_trace import SlTrace
from select_player import SelectPlayer

    
class PlayerControl(Toplevel):
    CONTROL_NAME_PREFIX = "player_control"
    DEF_WIN_X = 500
    DEF_WIN_Y = 300
    
    ###@profile
    def __init__(self, ctlbase=None,
                control_prefix=None,
                title=None, display=True):
        """ Display / Control of players
        :ctlbase: base control object
        
        values stored in properties file
        All values stored under "player_control.".<player_id>
        The player_id is constructed by replacing all
        sequences of [^a-zA-Z_0-9]+ by "_" in the player name
        to produce a legal properties file id string
        Value strings:
            id                  value type
            ------------        -------------
            name                string
            label               string
            playing             bool
            position            int
            mV                  int
            color               string (fill)
            voice               bool
            help_play           bool
            pause               float
            auto                bool
            level               int
            steven              float
        """
        ###Toplevel.__init__(self, parent)
        self.ctlbase = ctlbase
        if control_prefix is None:
            control_prefix = self.CONTROL_NAME_PREFIX
        self.control_prefix = control_prefix
        """ Setup control names found in properties file
        Updated as new control entries are added
        """
        prop_keys = SlTrace.getPropKeys()
        player_pattern = r'(?:\.(\w+))'
        pattern = (self.control_prefix
                    + player_pattern + player_pattern)
        rpat = re.compile(pattern)
        self.players = {}   # Dictionary of SelectPlayer
        self.cur_player = None   # Current player
        
                            # by name
        self.call_d = []    # Call back routines, if any
        for prop_key in prop_keys:
            rmatch = re.match(rpat, prop_key)
            if rmatch:
                player_match = rmatch[0]
                player_match_1 = rmatch[1]
                player_id = int(rmatch[1])
                player_field = rmatch[2]
                prop_val = SlTrace.getProperty(prop_key)
                
                if player_id not in self.players:
                    player = SelectPlayer(self, player_id)
                    self.players[player_id] = player # New entry
                else:
                    player = self.players[player_id]
                player_attr = rmatch[2]
                if player_attr == "move":
                    player_attr = "position"
                if not hasattr(player, player_attr):
                    raise SelectError("Unrecognized player attribute %s in %s"
                                      % (player_attr, prop_key))
                else:
                    pat = getattr(player, player_attr)
                    if isinstance(pat, float):
                        player_val = float(prop_val)
                    elif isinstance(pat, bool):
                        pvl = prop_val.lower()
                        if (pvl == "yes"
                                or pvl == "y"
                                or pvl == "1"
                                or pvl == "true"):
                            player_val = True
                        elif (pvl == "no"
                                or pvl == "n"
                                or pvl == "0"
                                or pvl == "false"):
                            player_val = False
                        else:
                            raise SelectError("Unrecognized boolean value (%s =)  %s"
                                              % (player_attr, prop_val))
                    elif isinstance(pat, int):
                        prop_val = float(prop_val)  # incase n.0
                        player_val = int(prop_val)
                    else:
                        player_val = prop_val
                    setattr(player, player_attr, player_val)
                    if player_attr == "color":
                        player.icolor =  player.color
                    elif player_attr == "color_bg":
                        player.icolor2 = player.color_bg
                    self.players[player_id] = player
        
        if title is None:
            title = "Player Control"
        self.title = title
        
        if display:
            self.control_display()
            
    ###@profile
    def control_display(self):
        """ display /redisplay controls to enable
        entry / modification
        """
        self.mw = Toplevel()

        self.mw.title(self.title)
        top_frame = Frame(self.mw)
        self.mw.protocol("WM_DELETE_WINDOW", self.delete_window)
        top_frame.pack(side="top", fill="x", expand=True)
        self.top_frame = top_frame
        
        controls_frame = Frame(top_frame)
        controls_frame.pack(side="top", fill="x", expand=True)
        self.controls_frame = controls_frame
        players_frame = Frame(controls_frame)
        players_frame.pack(side="top", fill="x", expand=True)
        class ColumnInfo:
            def __init__(self, field_name,
                         hd=None, width=None):
                """ column info
                :field_name: - SelectPlayer field name
                :hd: heading default: field_name.capitalized()
                :width: width in characters
                        default: length of heading + 1
                """
                self.field_name = field_name
                if hd is None:
                    hd = field_name.capitalize()
                self.heading = hd
                if width is None:
                    width = len(self.heading) + 1
                self.width = width
                
                
        """ fields in the order to present """        
        player_fields = ["name", "label",
                         "playing",
                         "position",
                         "color", "color_bg",
                         "voice", "help_play", "pause",
                         "auto", "level", "steven"]
        col_infos = []
        for field in player_fields:
            heading = self.get_heading(field)
            width = self.get_col_width(field)
            col_info = ColumnInfo(field, hd=heading, width=width)
            col_infos.append(col_info)
            
            
        self.set_field_headings(players_frame, col_infos)
        for pid, player in self.players.items():
            for idx, field in enumerate(player_fields):
                self.set_player_frame(players_frame, player, col_infos, idx)
            players_frame.rowconfigure(pid, weight=1)

        self.set_vals()     # Emphasize playing

        """ Contol buttons """
        control_button_frame = Frame(controls_frame)
        control_button_frame.pack(side="top", fill="x", expand=True)
        set_button = Button(master=control_button_frame, text="Set", command=self.set)
        set_button.pack(side="left", expand=True)
        add_button = Button(master=control_button_frame, text="Add",
                            command=self.add_player)
        add_button.pack(side="left", expand=True)
        delete_button = Button(master=control_button_frame, text="Delete",
                            command=self.delete_player)
        delete_button.pack(side="left", expand=True)

        self.mw.bind( '<Configure>', self.win_size_event)
        self.arrange_windows()


    def win_size_event(self, event):
        """ Window sizing event
        """
        win_x = self.mw.winfo_x()
        win_y = self.mw.winfo_y()
        win_width = self.mw.winfo_width()
        win_height = self.mw.winfo_height()
        self.set_prop_val("win_x", win_x)
        self.set_prop_val("win_y", win_y)
        self.set_prop_val("win_width", win_width)
        self.set_prop_val("win_height", win_height)


       
    
    ###@profile
    def arrange_windows(self):
        """ Arrange windows
            Get location and size for properties if any
        """
        win_x = self.get_prop_val("win_x", self.DEF_WIN_X)
        if win_x < 0:
            win_x = 50
        win_y = self.get_prop_val("win_y", self.DEF_WIN_Y)
        if win_y < 0:
            win_y = 50
        
        win_width = self.get_prop_val("win_width", self.mw.winfo_width())
        win_height = self.get_prop_val("win_height", self.mw.winfo_height())
        geo_str = "%dx%d+%d+%d" % (win_width, win_height, win_x, win_y)
        self.mw.geometry(geo_str)
        
    
    def get_prop_key(self, name):
        """ Translate full  control name into full Properties file key
        """        
        key = self.control_prefix + "." + name
        return key

    def get_prop_val(self, name, default):
        """ Get property value as (string)
        :name: field name
        :default: default value, if not found
        :returns: "" if not found
        """
        prop_key = self.get_prop_key(name)
        prop_val = SlTrace.getProperty(prop_key)
        if prop_val is None:
            return default
        
        if isinstance(default, int):
            if prop_val == "":
                return 0
           
            return int(prop_val)
        elif isinstance(default, float):
            if prop_val == "":
                return 0.
           
            return float(prop_val)
        else:
            return prop_val

    def set_prop_val(self, name, value):
        """ Set property value as (string)
        :name: field name
        :value: default value, if not found
        """
        prop_key = self.get_prop_key(name)
        SlTrace.setProperty(prop_key, str(value))



    def get_next_player(self, set_player=True):
        """ get next candidate player
        :set: True set as true default set as current player
        """
        SlTrace.lg("get_next_player, set_player=%s"
                   % set_player, "execute")
        prev_player = self.cur_player
        if self.cur_player is None:
            next_position = self.get_first_position()
        else:
            next_position = self.get_next_position(self.cur_player.position)
        player = self.get_player(next_position)
        
        
        if player is None:
            raise SelectError("No player playing with next position: %d"
                          % next_position)
        if set_player:    
            self.set_player(player)
            SlTrace.lg("new player: %s previous: %s" % (player, prev_player), "player")
        return player
    
    
    def get_first_position(self):
        position = None
        for player in self.players.values():
            if player.playing:
                if (player.position is not None
                        and (position is None or position > player.position)):
                    position = player.position
         
        if position is None:
            raise SelectError("No players")
        
        return position
    
    
    def get_next_position(self, position):
        """ Get next position after given,
        among playing players, wrapping if necessary
        """
        next_position = None
        for player in self.players.values():
            if player.playing and player.position is not None:
                if next_position is None:
                    if player.position > position:
                        next_position = player.position
                else:
                    if player.position > position:
                        if  player.position < next_position:
                            next_position = player.position
        if next_position is None:
            next_position = self.get_first_position()

        if next_position is None:
            raise SelectError("No players")
        
        return next_position


    def set_player(self, player):
        """ Record player  as next player
        """
        self.cur_player = player

        
    
    def get_player(self, position=None):
        """ Get player / current player
        Doesn't alter current player
        :position: position number
            default: current player
        """
        if position is not None:
            for player in self.players.values():
                if player.playing and player.position is not None:
                    if position == player.position:
                        return player
            raise SelectError("No player for position %s" % position)
        
        if self.cur_player is None:
            self.cur_player = self.get_next_player()
        return self.cur_player



  
    def get_player_prop_key(self, player):
        """ Generate full properties name for this player
        """
        key = self.get_prop_key(player.id)
        return key
        
    
    def get_players(self, all=False):
        """ Get players
        :all: all players default: just currently playing
        """
        players = []
        for player in self.players.values():
            if all or player.playing:
                players.append(player)
        return players
    

    def set(self):
        """ Set info from form
        """
        self.set_vals()
        
        
    def add_player(self):
        """ Add new player
        """
        SlTrace.lg("add_player not yet implemented")
    
    def delete_player(self):
        """ Delete player
        """
        SlTrace.lg("delete_player not yet implemented")
        
        
        
    def set_field_headings(self, field_headings_frame, col_infos):
        """ Setup player headings, possibly recording widths
        """
        for info_idx, col_info in enumerate(col_infos):
            field_name = col_info.field_name
            heading = col_info.heading
            heading_label = Label(master=field_headings_frame,
                                  text=heading, anchor=CENTER,
                                  justify=CENTER,
                                  width=col_info.width)
            heading_label.grid(row=0, column=info_idx, sticky=NSEW)
            field_headings_frame.columnconfigure(info_idx, weight=1)


    def get_col_width(self, field_name):
        """ Calculate widget text width
        :field_name: field name SelectPlayer attribute
        :returns:  proper column width, given heading and all values for this field
        """
        heading = self.get_heading(field_name)
        width = len(heading)        # Start with heading as width
        for player in self.players.values():
            val = getattr(player, field_name)
            val_len = len(str(val)) + 1
            if val_len > width:
                width = val_len
        return int(width*1.25)

    
    def get_field_name(self, heading):
        """ Convert heading into field name
        :heading:  Heading text
        """
        field = heading.lower()
        if field == "help":
            field = "help_play"
        return field

    
    def get_heading(self, field_name):
        """ Convert heading into field name
        :field_name:  field attribute
        """
        heading = field_name
        if heading == "help_play":
            heading = "help"
        heading = heading.capitalize()
        return heading
    

    ###@profile
    def set_player_frame(self, frame, player, col_infos, idx):
        """ Create player info line
        :frame: players frame
        :player: player info
        :col_infos: list of information for each column
        :idx: index into col_infos
        """
        col_info = col_infos[idx]
        field_name = col_info.field_name
        value = player.get_val(field_name)
        width = self.get_col_width(field_name)
        frame = Frame(frame, height=1, width=width)
        frame.grid(row=player.id, column=idx, sticky=NSEW)

        if field_name == "name":
            self.set_player_frame_name(frame, player, value, width=width)
        elif field_name == "label":
            self.set_player_frame_label(frame, player, value, width=width)
        elif field_name == "playing":
            self.set_player_frame_playing(frame, player, value, width=width)
        elif field_name == "position":
            self.set_player_frame_position(frame, player, value, width=width)
        elif field_name == "color":
            self.set_player_frame_color(frame, player, value, width=width)
        elif field_name == "color_bg":
            self.set_player_frame_color_bg(frame, player, value, width=width)
        elif field_name == "voice":
            self.set_player_frame_voice(frame, player, value, width=width)
        elif field_name == "help_play":
            self.set_player_frame_help(frame, player, value, width=width)
        elif field_name == "pause":
            self.set_player_frame_pause(frame, player, value, width=width)
        elif field_name == "auto":
            self.set_player_frame_auto(frame, player, value, width=width)
        elif field_name == "level":
            self.set_player_frame_level(frame, player, value, width=width)
        elif field_name == "steven":
            self.set_player_frame_steven(frame, player, value, width=width)
        else:
            raise SelectError("Unrecognized player field_name: %s" % field_name)    

    def get_num_playing(self):
        """ Calculate number playing
        """
        nplaying = 0
        for player in self.players.values():
            if player.playing:
                nplaying += 1
        return nplaying
    
    
            

    def set_player_frame_name(self, frame, player, value, width=None):
        content = StringVar()
        content.set(value)
        val_entry = Entry(frame, textvariable=content, width=width)
        val_entry.pack(side="left", fill="none", expand=True)
        player.ctls["name"] = val_entry
        player.ctls_vars["name"] = content

    def set_player_frame_label(self, frame, player, value, width=None):
        content = StringVar()
        content.set(value)
        val_entry = Entry(frame, textvariable=content, width=width)
        val_entry.pack(side="left", fill="none", expand=True)
        player.ctls["label"] = val_entry
        player.ctls_vars["label"] = content

    def set_player_frame_playing(self, frame, player, value, width=None):
        content = BooleanVar()
        content.set(value)
        yes_button = Checkbutton(frame, variable=content, width=None)
        yes_button.pack(side="left", fill="none", expand=True)
        player.ctls["playing"] = yes_button
        player.ctls_vars["playing"] = content

    def set_player_frame_position(self, frame, player, value, width=None):
        content = IntVar()
        content.set(value)
        yes_button = Entry(frame, textvariable=content, width=width)
        yes_button.pack(side="left", expand=True)
        player.ctls["position"] = yes_button
        player.ctls_vars["position"] = content

    def set_player_frame_color(self, frame, player, value, width=None):
        content = StringVar()
        content.set(value)
        val_entry = Entry(frame, textvariable=content, width=width)
        val_entry.pack(side="left", fill="none", expand=True)
        player.ctls["color"] = val_entry
        player.ctls_vars["color"] = content

    def set_player_frame_color_bg(self, frame, player, value, width=None):
        content = StringVar()
        content.set(value)
        val_entry = Entry(frame, textvariable=content, width=width)
        val_entry.pack(side="left", fill="none", expand=True)
        player.ctls["color_bg"] = val_entry
        player.ctls_vars["color_bg"] = content

    def set_player_frame_voice(self, frame, player, value, width=None):
        content = BooleanVar()
        content.set(value)
        yes_button =  Checkbutton(frame, variable=content, width=width)
        yes_button.pack(side="left", fill="none", expand=True)
        player.ctls["voice"] = yes_button
        player.ctls_vars["voice"] = content

    def set_player_frame_help(self, frame, player, value, width=None):
        content = BooleanVar()
        content.set(value)
        yes_button = Checkbutton(frame, variable=content, width=width)
        yes_button.pack(side="left", fill="none", expand=True)
        player.ctls["help_play"] = yes_button
        player.ctls_vars["help_play"] = content

    def set_player_frame_pause(self, frame, player, value, width=None):
        content = DoubleVar()
        content.set(value)
        yes_button = Entry(frame, textvariable=content, width=width)
        yes_button.pack(side="left", expand=True)
        player.ctls["pause"] = yes_button
        player.ctls_vars["pause"] = content

    def set_player_frame_auto(self, frame, player, value, width=None):
        content = BooleanVar()
        content.set(value)
        yes_button = Checkbutton(frame, variable=content, width=width)
        yes_button.pack(side="left", fill="none", expand=True)
        player.ctls["auto"] = yes_button
        player.ctls_vars["auto"] = content

    def set_player_frame_level(self, frame, player, value, width=None):
        content = IntVar()
        content.set(value)
        yes_button = Entry(frame, textvariable=content, width=width)
        yes_button.pack(side="left", expand=True)
        player.ctls["level"] = yes_button
        player.ctls_vars["level"] = content

    def set_player_frame_steven(self, frame, player, value, width=None):
        content = DoubleVar()
        content.set(value)
        yes_button = Entry(frame, textvariable=content, width=width)
        yes_button.pack(side="left", expand=True)
        player.ctls["steven"] = yes_button
        player.ctls_vars["steven"] = content


    def set_ctls(self):
        """ Update control/display from internal values
        of those playing
        """
        for player in self.players.values():
            if player.playing:
                player.set_ctls()


    def set_vals(self):
        """ Read form, if displayed, and update internal values
        """
        for player in self.players.values():
            is_playing = player.playing
            for field in player.ctls_vars:
                player.set_val_from_ctl(field)
                field_ctl = player.ctls[field]
                if is_playing:
                    field_ctl.config({"bg" : "white"})
                else:
                    field_ctl.config({"bg" : "light gray"})


    def set_score(self, player, score):
        """ Set player score centrally 
        :player: to set
        :score: to set
        """
        cplayer = self.players[player.id]
        player.score = score        # Set possible copy
        cplayer.score = score


    def get_score(self, player):
        """ Get player score centrally 
        :player: to get
        """
        cplayer = self.players[player.id]
        return cplayer.score


    def set_played(self, player, played):
        """ Set player game centrally 
        :player: to set
        :played: to set
        """
        cplayer = self.players[player.id]
        player.played = played        # Set possible copy
        cplayer.played = played


    def get_played(self, player):
        """ Get player game centrally 
        :player: to get
        """
        cplayer = self.players[player.id]
        return cplayer.played


    def get_ties(self, player):
        """ Get player game centrally 
        :player: to get
        """
        cplayer = self.players[player.id]
        return cplayer.ties


    def set_ties(self, player, ties):
        """ Set player game centrally 
        :player: to set
        :ties: to set
        """
        cplayer = self.players[player.id]
        player.ties = ties        # Set possible copy
        cplayer.ties = ties


    def get_wins(self, player):
        """ Get player game centrally 
        :player: to get
        """
        cplayer = self.players[player.id]
        return cplayer.wins


    def set_wins(self, player, wins):
        """ Set player game centrally 
        :player: to set
        :wins: to set
        """
        cplayer = self.players[player.id]
        player.wins = wins        # Set possible copy
        cplayer.wins = wins
        
        
    def set_all_scores(self, score=0, only_playing=False):
        """ Set all player scores
        :score: player score default: 0
        :only_playing: only modify those playing default: all
        """
        for _, player in self.players.items():
            if only_playing and not player.playing:
                continue    # Not playing - leave alone
            player.set_score(score)

    def set_all_played(self, played=0, only_playing=False):
        """ Set all player played
        :played: player played default: 0
        :only_playing: only modify those playing default: all
        """
        for _, player in self.players.items():
            if only_playing and not player.playing:
                continue    # Not playing - leave alone
            player.set_played(played)

    def set_all_wins(self, wins=0, only_playing=False):
        """ Set all player wins
        :wins: player wins default: 0
        :only_playing: only modify those playing default: all
        """
        for _, player in self.players.items():
            if only_playing and not player.playing:
                continue    # Not playing - leave alone
            player.set_wins(wins)
       
    def delete_window(self):
        """ Process Trace Control window close
        """
        if self.mw is not None:
            self.mw.destroy()
            self.mw = None

    def destroy(self):
        """ relinquish resources
        """
        self.delete_window()
        
        
    
    def add(self):
        if "set" in self.call_d:
            self.call_d["set"]()
    
    def edit(self):
        if "edit" in self.call_d:
            self.call_d["edit"]()
        
    def delete(self):
        if "delete" in self.call_d:
            self.call_d["delete"]()
    

        
if __name__ == '__main__':
        
    root = Tk()

    frame = Frame(root)
    frame.pack()
    SlTrace.setProps()
    SlTrace.setFlags("")
    plc = PlayerControl(frame, title="player_control", display=True)
        
    root.mainloop()