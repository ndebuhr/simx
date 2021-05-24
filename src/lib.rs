extern crate proc_macro;

use proc_macro::TokenStream;
use quote::{quote};
use serde::{Deserialize, Serialize};
use syn::{parse_macro_input, Expr, ExprIf, ItemImpl, ImplItem, Stmt};

#[derive(Debug, Deserialize, Serialize)]
struct EventRule {
    event_expression: String,
    event_routine: EventRoutine,
}

#[derive(Debug, Deserialize, Serialize)]
enum EventRoutine {
    ConditionalScheduling(Vec<ConditionalScheduling>),
    UnconditionalStateTransition(String),
}

#[derive(Debug, Deserialize, Serialize)]
struct ConditionalScheduling {
    follow_up_event: String,
    condition: String,
}

impl EventRule {
    fn new_conditional_scheduling(event_expression: String, conditional_schedulings: Vec<ConditionalScheduling>) -> Self {
        Self {
            event_expression,
            event_routine: EventRoutine::ConditionalScheduling(conditional_schedulings),
        }
    }

    fn new_unconditional_state_transition(event_expression: String, event_routine: String) -> Self {
        Self {
            event_expression,
            event_routine: EventRoutine::UnconditionalStateTransition(event_routine),
        }
    }
}

#[proc_macro_attribute]
pub fn event_rules(_attr: TokenStream, item: TokenStream) -> TokenStream {
    let input = parse_macro_input!(item as ItemImpl);
    let output = TokenStream::from(quote!(#input));

    // Check to see if we have an impl AsModel for NewModel, an impl NewModel, or something else
    let mut is_impl = false;
    let mut is_impl_as_model = false;
    if let None = &input.trait_ {
        is_impl = true;
    } else if let Some(trait_) = &input.trait_ {
        if trait_.1.segments[0].ident.to_string() == "AsModel" {
            is_impl_as_model = true;
        }
    }

    let mut event_rules = Vec::new();

    // Get the unconditional state transition event rules if is_impl
    if is_impl {
        input.items.iter()
            .filter_map(|method| {
                if let ImplItem::Method(method) = method {
                    Some(method)
                } else {
                    None
                }
            })
            .for_each(|method| {
                let name = &method.sig.ident;
                let routine = &method.block;
                event_rules.push(
                    EventRule::new_unconditional_state_transition(
                        quote!(#name).to_string(),
                        quote!(#routine).to_string(),
                    )
                )
            });
    }

    // Get the conditional scheduling event rules if is_impl_as_model
    if is_impl_as_model {
        // populate events_ext
        input.items.iter()
            .filter_map(|method| {
                if let ImplItem::Method(method) = method {
                    Some(method)
                } else {
                    None
                }
            })
            .filter(|method| {
                &method.sig.ident.to_string() == "events_ext"
            })
            .for_each(|method| {
                // [0] assumes the event_ext and event_int starts with a if block
                if let Stmt::Expr(expr) = &method.block.stmts[0] {
                    if let Expr::If(if_) = expr {
                        let mut conditional_schedulings = Vec::new();
                        // Approach assumes the final else case is an error return
                        extract_ext_cases(&mut conditional_schedulings, if_);
                        event_rules.push(
                            EventRule::new_conditional_scheduling(
                                String::from("events_ext"),
                                conditional_schedulings,
                            )
                        )
                    }
                }
            });
        // populate events_int
        input.items.iter()
            .filter_map(|method| {
                if let ImplItem::Method(method) = method {
                    Some(method)
                } else {
                    None
                }
            })
            .filter(|method| {
                &method.sig.ident.to_string() == "events_int"
            })
            .for_each(|method| {
                // [0] assumes the event_ext and event_int starts with a if block
                if let Stmt::Expr(expr) = &method.block.stmts[0] {
                    if let Expr::If(if_) = expr {
                        let mut conditional_schedulings = Vec::new();
                        // Approach assumes the final else case is an error return
                        extract_int_cases(&mut conditional_schedulings, if_);
                        event_rules.push(
                            EventRule::new_conditional_scheduling(
                                String::from("events_int"),
                                conditional_schedulings,
                            )
                        )
                    }
                }
            });
    }
    println!["{:?}", serde_json::to_string(&event_rules).unwrap()];
    output
}

fn extract_ext_cases(cases: &mut Vec<ConditionalScheduling>, expr_if: &ExprIf) {
    let cond = &expr_if.cond;
    if let Stmt::Semi(expr, _) = &expr_if.then_branch.stmts[0] {
        if let Expr::Try(expr_try) = expr {
            if let Expr::MethodCall(method_call) = &*expr_try.expr {
                let method = &method_call.method;
                cases.push(
                    ConditionalScheduling{
                        follow_up_event: quote!(#method).to_string(),
                        condition: quote!(#cond).to_string(),
                    }
                )
            }
        }
    }
    let else_branch = &expr_if.else_branch;
    if let Some(else_) = else_branch {
        if let Expr::If(next_branch) = &*else_.1 {
            extract_ext_cases(cases, &next_branch)
        }
    }
}

fn extract_int_cases(cases: &mut Vec<ConditionalScheduling>, expr_if: &ExprIf) {
    let cond = &expr_if.cond;
    if let Stmt::Expr(expr) = &expr_if.then_branch.stmts[0] {
        if let Expr::MethodCall(method_call) = expr {
            let method = &method_call.method;
            cases.push(
                ConditionalScheduling{
                    follow_up_event: quote!(#method).to_string(),
                    condition: quote!(#cond).to_string(),
                }
            )
        }
    }
    let else_branch = &expr_if.else_branch;
    if let Some(else_) = else_branch {
        if let Expr::If(next_branch) = &*else_.1 {
            extract_int_cases(cases, &next_branch)
        }
    }
}