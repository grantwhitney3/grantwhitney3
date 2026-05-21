{
	"patcher" : {
		"fileversion" : 1,
		"appversion" : {
			"major" : 8,
			"minor" : 6,
			"revision" : 0,
			"architecture" : "x64",
			"modernui" : 1
		},
		"classnamespace" : "box",
		"rect" : [ 100.0, 100.0, 640.0, 430.0 ],
		"bglocked" : 0,
		"openinpresentation" : 1,
		"default_fontsize" : 12.0,
		"default_fontface" : 0,
		"default_fontname" : "Arial",
		"gridonopen" : 1,
		"gridsize" : [ 15.0, 15.0 ],
		"gridsnaponopen" : 1,
		"objectsnaponopen" : 1,
		"statusbarvisible" : 2,
		"toolbarvisible" : 1,
		"lefttoolbarpinned" : 0,
		"toptoolbarpinned" : 0,
		"righttoolbarpinned" : 0,
		"bottomtoolbarpinned" : 0,
		"toolbars_unpinned_last_save" : 0,
		"tallnewobj" : 0,
		"boxanimatetime" : 200,
		"enablehscroll" : 1,
		"enablevscroll" : 1,
		"devicewidth" : 0.0,
		"description" : "Max for Live MIDI effect patch that lights a UI toggle when MIDI note C3 is played.",
		"digest" : "Detect C3 MIDI note and flash UI",
		"tags" : "midi,ableton,max-for-live,c3",
		"boxes" : [
			{
				"box" : {
					"id" : "obj-1",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 35.0, 25.0, 430.0, 20.0 ],
					"text" : "C3 MIDI Detector - drop into a Max for Live MIDI Effect"
				}
			},
			{
				"box" : {
					"id" : "obj-2",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 35.0, 50.0, 510.0, 20.0 ],
					"text" : "C3 in Ableton is MIDI note 60. Change the number in [sel 60] if your note naming differs."
				}
			},
			{
				"box" : {
					"id" : "obj-3",
					"maxclass" : "newobj",
					"numinlets" : 1,
					"numoutlets" : 3,
					"outlettype" : [ "int", "int", "int" ],
					"patching_rect" : [ 70.0, 105.0, 48.0, 22.0 ],
					"text" : "notein"
				}
			},
			{
				"box" : {
					"id" : "obj-4",
					"maxclass" : "newobj",
					"numinlets" : 3,
					"numoutlets" : 0,
					"patching_rect" : [ 295.0, 105.0, 55.0, 22.0 ],
					"text" : "noteout"
				}
			},
			{
				"box" : {
					"id" : "obj-5",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 2,
					"outlettype" : [ "int", "int" ],
					"patching_rect" : [ 70.0, 160.0, 62.0, 22.0 ],
					"text" : "stripnote"
				}
			},
			{
				"box" : {
					"id" : "obj-6",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 2,
					"outlettype" : [ "bang", "" ],
					"patching_rect" : [ 70.0, 215.0, 45.0, 22.0 ],
					"text" : "sel 60"
				}
			},
			{
				"box" : {
					"id" : "obj-7",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 70.0, 270.0, 29.5, 22.0 ],
					"text" : "1"
				}
			},
			{
				"box" : {
					"id" : "obj-8",
					"maxclass" : "newobj",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "bang" ],
					"patching_rect" : [ 150.0, 270.0, 68.0, 22.0 ],
					"text" : "delay 150"
				}
			},
			{
				"box" : {
					"id" : "obj-9",
					"maxclass" : "message",
					"numinlets" : 2,
					"numoutlets" : 1,
					"outlettype" : [ "" ],
					"patching_rect" : [ 150.0, 320.0, 29.5, 22.0 ],
					"text" : "0"
				}
			},
			{
				"box" : {
					"id" : "obj-10",
					"maxclass" : "toggle",
					"numinlets" : 1,
					"numoutlets" : 1,
					"outlettype" : [ "int" ],
					"parameter_enable" : 0,
					"patching_rect" : [ 70.0, 335.0, 46.0, 46.0 ],
					"presentation" : 1,
					"presentation_rect" : [ 35.0, 35.0, 46.0, 46.0 ]
				}
			},
			{
				"box" : {
					"id" : "obj-11",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 130.0, 348.0, 150.0, 20.0 ],
					"presentation" : 1,
					"presentation_rect" : [ 95.0, 48.0, 120.0, 20.0 ],
					"text" : "C3 detected"
				}
			},
			{
				"box" : {
					"id" : "obj-12",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 365.0, 105.0, 210.0, 20.0 ],
					"text" : "passes all MIDI notes through unchanged"
				}
			},
			{
				"box" : {
					"id" : "obj-13",
					"maxclass" : "comment",
					"numinlets" : 1,
					"numoutlets" : 0,
					"patching_rect" : [ 230.0, 270.0, 225.0, 20.0 ],
					"text" : "flash for 150 ms on each C3 note-on"
				}
			}
		],
		"lines" : [
			{
				"patchline" : {
					"source" : [ "obj-3", 0 ],
					"destination" : [ "obj-5", 0 ]
				}
			},
			{
				"patchline" : {
					"source" : [ "obj-3", 1 ],
					"destination" : [ "obj-5", 1 ]
				}
			},
			{
				"patchline" : {
					"source" : [ "obj-3", 0 ],
					"destination" : [ "obj-4", 0 ]
				}
			},
			{
				"patchline" : {
					"source" : [ "obj-3", 1 ],
					"destination" : [ "obj-4", 1 ]
				}
			},
			{
				"patchline" : {
					"source" : [ "obj-3", 2 ],
					"destination" : [ "obj-4", 2 ]
				}
			},
			{
				"patchline" : {
					"source" : [ "obj-5", 0 ],
					"destination" : [ "obj-6", 0 ]
				}
			},
			{
				"patchline" : {
					"source" : [ "obj-6", 0 ],
					"destination" : [ "obj-7", 0 ]
				}
			},
			{
				"patchline" : {
					"source" : [ "obj-6", 0 ],
					"destination" : [ "obj-8", 0 ]
				}
			},
			{
				"patchline" : {
					"source" : [ "obj-8", 0 ],
					"destination" : [ "obj-9", 0 ]
				}
			},
			{
				"patchline" : {
					"source" : [ "obj-7", 0 ],
					"destination" : [ "obj-10", 0 ]
				}
			},
			{
				"patchline" : {
					"source" : [ "obj-9", 0 ],
					"destination" : [ "obj-10", 0 ]
				}
			}
		]
	}
}
